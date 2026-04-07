# AI Agent 实现机制文档

## 1. 整体架构

AI Agent 模块采用 **ReAct（Reasoning + Acting）** 循环架构，基于 LangChain 框架构建。整体架构如下：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI Chat Service                                 │
│  (编排 Agent + Memory + Tools，处理 SSE 流式响应)                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
│ AgentExecutor│     │ MemoryManager   │    │ Tool Registry   │    │    LLM      │
│ (ReAct循环) │     │ (记忆管理)      │    │ (工具注册)      │    │ (DeepSeek) │
└─────────────┘     └─────────────────┘    └─────────────────┘    └─────────────┘
         │                    │                    │                    │
         │                    ▼                    │                    │
         │           ┌─────────────────┐           │                    │
         │           │ SummaryBuffer   │           │                    │
         │           │ (Redis缓冲)     │           │                    │
         │           └─────────────────┘           │                    │
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    持久化层 (MongoDB + Redis)                                │
│  - ChatLog: 消息记录                                                         │
│  - AiSummary: 对话摘要                                                       │
│  - Redis Buffer: 最近对话缓冲                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. 核心组件说明

### 2.1 AgentExecutor (app/ai/agent.py)

**核心职责**：执行 ReAct 循环，处理 LLM 调用和工具执行。

**工作流程**：

1. 接收用户消息，构建消息列表（系统提示词 + 记忆消息 + 用户消息）
2. 调用 LLM，检测是否返回 `tool_calls`
3. 如果有工具调用：
   - 执行工具，通过回调推送 `ai_tool_call` 和 `ai_tool_result` 事件
   - 将工具结果回传给 LLM，继续循环
4. 如果无工具调用，推送最终回答（`ai_chunk` + `ai_complete`）
5. 最大轮次保护（默认 10 轮）

**关键参数**：
```python
MAX_TOOL_ROUNDS = 10          # 最大工具调用轮次
MAX_MESSAGE_LENGTH = 4000     # 用户消息最大长度
CHUNK_SIZE = 10               # 流式输出分片大小
```

### 2.2 LLM 配置 (app/ai/llm.py)

**两种 LLM 实例**：

| 用途 | 模型 | 参数配置 |
|------|------|----------|
| Chat LLM | `deepseek-chat` | temperature=0.7, max_tokens=4096, streaming=true |
| Summary LLM | `deepseek-chat` | temperature=0.3, max_tokens=1024, streaming=false |

**配置来源**：
```python
DEEPSEEK_API_KEY: str = ""                    # API密钥
DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
DEEPSEEK_MODEL: str = "deepseek-chat"
AI_TIMEOUT: int = 120                         # 超时时间（秒）
```

### 2.3 Tool Registry (app/ai/tools/registry.py)

**可用工具列表**：

| 工具类别 | 工具名称 | 功能描述 |
|----------|----------|----------|
| 时间解析 | `parseTime` | 自然语言时间转时间戳 |
| 时间解析 | `getCurrentTime` | 获取当前时间 |
| 用户查询 | `getUserByName` | 通过用户名查找用户 |
| 部门查询 | `getDepartmentTree` | 获取部门树 |
| 部门查询 | `getDepartmentInfo` | 获取部门详情 |
| 待办管理 | `createTodo` | 创建待办事项 |
| 待办管理 | `findTodos` | 查询待办列表 |
| 审批管理 | `createApproval` | 创建审批申请 |
| 审批管理 | `findApprovals` | 查询审批列表 |

**工具注入机制**：通过闭包注入当前用户上下文（user_id, user_name），确保工具执行时的权限隔离。

## 3. 记忆系统设计

### 3.1 记忆架构

采用 **摘要缓冲混合策略**，结合 Redis 缓冲和 MongoDB 持久化：

```
┌────────────────────────────────────────────────────────────┐
│                    MemoryManager                            │
│                                                            │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │ Redis Summary   │    │ Redis Buffer    │               │
│  │ (对话摘要缓存)  │    │ (最近对话缓冲)  │               │
│  │ TTL: 24h        │    │ TTL: 24h        │               │
│  └─────────────────┘    └─────────────────┘               │
│           │                      │                        │
│           ▼                      ▼                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              MongoDB 持久化                          │  │
│  │  - AiSummary: 摘要文档（长期记忆）                    │  │
│  │  - ChatLog: 完整对话记录（兜底加载）                  │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 3.2 记忆获取流程

```python
async def get_memory_messages(conversation_id: str) -> List[dict]:
    # 1. 获取摘要（Redis优先，MongoDB兜底）
    summary = await self._get_summary(conversation_id)
    if summary:
        messages.append({"role": "system", "content": f"[对话摘要]\n{summary}"})
    
    # 2. 获取最近对话缓冲
    buffer_messages = await self._buffer.get_buffer_messages(conversation_id)
    if not buffer_messages:
        # Redis为空，从MongoDB加载最近20条
        buffer_messages = await self._load_from_mongodb(conversation_id)
        # 回写到Redis
        for msg in buffer_messages:
            await self._buffer.add_message(conversation_id, msg["role"], msg["content"])
    
    messages.extend(buffer_messages)
    return messages
```

### 3.3 摘要压缩触发机制

**触发条件**：缓冲区字符数超过 `AI_MEMORY_MAX_TOKEN_LIMIT`（默认2000字符）

**压缩流程**：
1. 获取当前摘要 + 缓冲对话
2. 构建摘要请求消息
3. 调用 Summary LLM 生成新摘要
4. 保存到 MongoDB（AiSummary）和 Redis
5. 清空 Redis 缓冲区

**降级策略**：如果摘要生成失败，只保留最近10条消息。

### 3.4 Token 估算

采用字符数估算（而非精确 Token 计算）：
```python
def estimate_token_count(char_count: int) -> int:
    # 中文字符与 Token 比例约为 1:1.5
    return int(char_count * 1.5)
```

**注意**：配置项 `AI_MEMORY_MAX_TOKEN_LIMIT` 实际用于字符数限制。

## 4. 上下文窗口处理

### 4.1 消息构建流程

AgentExecutor 构建 LLM 消息的顺序：

```python
messages = [
    SystemMessage(content=system_prompt),      # 系统提示词（含用户上下文）
    ...memory_messages...,                      # 记忆消息（摘要 + 最近对话）
    HumanMessage(content=user_message),        # 当前用户消息
]
```

### 4.2 系统提示词注入

系统提示词预注入时间和用户信息，减少工具调用：

```python
def build_system_prompt(user_id: str, user_name: str) -> str:
    return f"""你是 AIWorkHelper 智能办公助手...
    
    ## 当前上下文
    - 当前用户：{user_name}（用户ID：{user_id}）
    - 当前时间：{now_cst}（时间戳：{current_ts} 毫秒）
    - 明天 0 点时间戳：{tomorrow_ts} 毫秒
    - 时间计算公式：目标时间戳 = 明天 0 点时间戳 + (小时 * 3600 + 分钟 * 60) * 1000
    ...
    """
```

### 4.3 上下文窗口限制策略

| 策略 | 触发条件 | 处理方式 |
|------|----------|----------|
| 摘要压缩 | 缓冲区 > 2000字符 | LLM生成摘要，清空缓冲 |
| 降级保留 | 摘要生成失败 | 仅保留最近10条消息 |
| 消息截断 | 用户消息 > 4000字符 | 返回错误提示 |
| 轮次保护 | 工具调用 > 10轮 | 终止对话，提示简化问题 |

### 4.4 记忆容量估算

- 摘要：约200字（约300 Token）
- 缓冲区：最大2000字符（约3000 Token）
- 系统提示词：约500 Token
- 用户消息：最大4000字符（约6000 Token）

**总上下文窗口估算**：约 10000 Token（DeepSeek 模型支持 64K Token，有充足余量）

## 5. 流式响应设计

### 5.1 SSE 事件类型

| 事件类型 | 数据结构 | 触发时机 |
|----------|----------|----------|
| `ai_chunk` | `{conversationId, content, index}` | 流式推送AI文本片段 |
| `ai_tool_call` | `{conversationId, tool, args, status}` | 工具调用开始 |
| `ai_tool_result` | `{conversationId, tool, result, status}` | 工具执行完成 |
| `ai_complete` | `{conversationId, content, messageId}` | AI响应完成 |
| `ai_error` | `{conversationId, error, message}` | 错误发生 |

### 5.2 SSE 推送机制

使用 `asyncio.Queue` 实现异步事件传递：

```python
# Agent 在后台任务中执行，通过 Queue 推送事件
async def _run_agent():
    executor = AgentExecutor(
        on_chunk=lambda c, i: queue.put(_sse_event("ai_chunk", {...})),
        on_tool_call=lambda n, a, s: queue.put(_sse_event("ai_tool_call", {...})),
        ...
    )
    await executor.run(content)
    await queue.put(sentinel)  # 结束标记

# Generator 从 Queue 中 yield SSE 事件
while True:
    item = await queue.get()
    if item is sentinel:
        break
    yield item
```

## 6. 配置参数汇总

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DEEPSEEK_API_KEY` | "" | DeepSeek API密钥 |
| `DEEPSEEK_BASE_URL` | "https://api.deepseek.com" | API地址 |
| `DEEPSEEK_MODEL` | "deepseek-chat" | 模型名称 |
| `AI_TIMEOUT` | 120 | LLM超时时间（秒） |
| `AI_MAX_TOOL_ROUNDS` | 10 | 最大工具调用轮次 |
| `AI_MEMORY_MAX_TOKEN_LIMIT` | 2000 | 缓冲区字符数上限 |
| `AI_MEMORY_REDIS_TTL` | 86400 | Redis缓存TTL（秒） |
| `AI_MAX_MESSAGE_LENGTH` | 4000 | 用户消息长度上限 |

## 7. 关键设计决策

### 7.1 为什么选择摘要缓冲混合策略？

1. **Redis 缓冲**：提供快速读写，减少 MongoDB 查询
2. **MongoDB 兜底**：Redis 缓存失效时可恢复记忆
3. **摘要压缩**：控制上下文窗口大小，避免 Token 超限
4. **降级策略**：摘要失败时保留最近消息，保证基本对话能力

### 7.2 为什么预注入时间上下文？

减少 `parseTime` 和 `getCurrentTime` 工具调用频率：
- 用户提到"明天3点"时，LLM可直接计算时间戳
- 仅复杂时间表达式才需要调用工具

### 7.3 为什么使用 asyncio.Queue？

SSE 流式响应要求 generator 不能阻塞 Agent 执行：
- Agent 在后台任务中运行
- 回调函数将事件写入 Queue
- Generator 从 Queue yield 事件

## 8. 文件结构

```
app/ai/
├── __init__.py
├── agent.py              # Agent执行器（ReAct循环）
├── llm.py                # LLM客户端封装
├── memory/
│   ├── __init__.py
│   ├── memory_manager.py # 记忆管理器（摘要+缓冲）
│   └── summary_buffer.py # Redis缓冲管理
├── prompts/
│   ├── __init__.py
│   └── system_prompt.py  # 系统提示词模板
└── tools/
    ├── __init__.py
    ├── registry.py       # 工具注册中心
    ├── time_tool.py      # 时间解析工具
    ├── user_tool.py      # 用户查询工具
    ├── department_tool.py # 部门查询工具
    ├── todo_tool.py      # 待办管理工具
    └── approval_tool.py  # 审批管理工具
```
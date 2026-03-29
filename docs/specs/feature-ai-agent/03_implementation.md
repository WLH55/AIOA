# Implementation: AI Agent 对话系统

## Execution Status (执行状态)

| 字段 | 值 |
|------|-----|
| **Phase** | Plan |
| **Progress** | 0/13 steps (0%) |
| **Current Task** | Step 1 - 依赖与配置 |
| **Last Updated** | 2026-03-29 |

---

## Objective (目标复述)

基于 LangChain + DeepSeek API 构建 AI Agent 对话系统。支持独立 AI 对话页面和群聊 @AI 两种入口，通过 Function Calling 自主调用 12 个系统工具（时间解析、待办、审批、用户、部门），实现自然语言驱动业务操作。多会话管理，滑动窗口 + 增量摘要上下文管理，数据持久化到 MongoDB + Redis 缓存。

## File Changes (变更范围)

### 新增文件

```
app/ai/
├── __init__.py
├── agent.py                          # Agent 核心循环（手动 ReAct）
├── llm.py                            # DeepSeek 客户端配置
├── memory/
│   ├── __init__.py
│   ├── memory_manager.py             # 多会话记忆管理器
│   └── summary_buffer.py             # 摘要缓冲实现
├── tools/
│   ├── __init__.py
│   ├── registry.py                   # 工具注册中心
│   ├── time_tool.py                  # parseTime + getCurrentTime
│   ├── todo_tool.py                  # createTodo + findTodos
│   ├── approval_tool.py              # 4 个审批工具
│   ├── user_tool.py                  # getUserByName
│   └── department_tool.py            # getDepartmentTree + getDepartmentInfo
└── prompts/
    ├── __init__.py
    └── system_prompt.py              # 系统提示词模板

app/models/
├── ai_conversation.py                # AI 会话模型
└── ai_summary.py                     # AI 摘要模型

app/repository/
├── ai_conversation_repository.py     # AI 会话 Repository
└── ai_summary_repository.py          # AI 摘要 Repository

app/dto/
├── ai/
│   ├── __init__.py
│   ├── ai_request.py                 # AI 会话请求 DTO
│   └── ai_response.py                # AI 会话响应 DTO
└── ws/
    └── ai_message.py                 # WebSocket AI 消息 DTO

app/services/
├── ai_conversation_service.py        # AI 会话管理服务
└── ai_chat_service.py                # AI 对话编排服务

app/routers/
└── ai.py                             # AI 会话路由
```

### 修改文件

```
requirements.txt                      # 新增 LangChain 依赖
app/config/settings.py                # 新增 AI 配置项
app/models/chat_log.py                # 确认 chatType=3 支持完整
app/dto/ws/message.py                 # 新增 AI 消息类型枚举
app/services/ws_manager.py            # 新增 AI 消息发送辅助方法
app/routers/ws.py                     # 新增 ai_chat 消息处理分支
app/main.py                           # 注册 AI 路由和 Beanie 模型
```

## Data Changes (数据变更)

- **表结构变更**：新增 `ai_conversation` 和 `ai_summary` 两个 MongoDB 集合
- **索引变更**：
  - ai_conversation: `userId + status` 复合索引, `updatedAt` 索引
  - ai_summary: `conversationId` 唯一索引
- **数据迁移**：无

## Core Logic (核心流程)

```
1. 用户通过 WebSocket 发送 ai_chat 消息
2. 主循环 create_task 异步派发，不阻塞正常聊天
3. AiChatService 编排处理：
   a. 获取/验证会话
   b. 从 MemoryManager 加载记忆（摘要 + 最近对话）
   c. 注入系统提示词（含时间上下文）
   d. 绑定当前用户专属工具集
   e. 手动 ReAct 循环：
      - 调用 LLM，流式推送 ai_chunk
      - 如果 LLM 返回 tool_call → 执行工具，推送 ai_tool_call/result，结果回传 LLM
      - 如果 LLM 返回最终回答 → 推送 ai_complete
   f. 保存用户消息和 AI 响应到 ChatLog
   g. 更新 Redis 对话缓冲
   h. 检查 Token 估算，超限则触发摘要压缩
```

## Key Validations (关键校验)

- 输入校验：conversationId 非空且属于当前用户，content 非空
- 业务校验：会话数量不超上限（50），会话状态为活跃
- 权限校验：工具调用继承当前用户权限（userId 注入）
- 异常处理：DeepSeek API 超时/失败推送 ai_error，摘要失败降级保留最近 10 条

## Execution Plan (分步计划)

> **状态图例**：完成 | 进行中 | 待开始 | 阻塞

---

### Step 1: 依赖与配置 ⏳

**任务清单**：
- [ ] requirements.txt 新增 LangChain 依赖
- [ ] settings.py 新增 AI 相关配置项
- [ ] .env.development 新增 AI 环境变量

**产出文件**：
- `requirements.txt`
- `app/config/settings.py`
- `.env.development`

**依赖说明**：
```
langchain>=0.3.0
langchain-openai>=0.3.0        # DeepSeek 兼容 OpenAI 接口
langchain-core>=0.3.0
```

---

### Step 2: 数据模型 ⏳

**任务清单**：
- [ ] 创建 AiConversation 模型（userId, title, status, createdAt, updatedAt）
- [ ] 创建 AiSummary 模型（conversationId, summary, charCount, createdAt, updatedAt）
- [ ] 定义模型索引

**产出文件**：
- `app/models/ai_conversation.py`
- `app/models/ai_summary.py`

---

### Step 3: Repository 层 ⏳

**任务清单**：
- [ ] 创建 AiConversationRepository（CRUD + 按用户分页查询 + 数量统计）
- [ ] 创建 AiSummaryRepository（按 conversationId 查询 + 创建/更新）

**产出文件**：
- `app/repository/ai_conversation_repository.py`
- `app/repository/ai_summary_repository.py`

---

### Step 4: DTO 层 ⏳

**任务清单**：
- [ ] 创建 AI 会话请求 DTO（CreateConversationRequest, DeleteConversationRequest）
- [ ] 创建 AI 会话响应 DTO（ConversationResponse, ConversationListResponse, MessageResponse）
- [ ] 创建 WebSocket AI 消息 DTO（AiChatMessage, AiChunkMessage, AiCompleteMessage, AiToolCallMessage, AiToolResultMessage, AiErrorMessage）
- [ ] 更新 ws/message.py 新增 AI 相关 MessageType 枚举

**产出文件**：
- `app/dto/ai/ai_request.py`
- `app/dto/ai/ai_response.py`
- `app/dto/ws/ai_message.py`
- `app/dto/ws/message.py`（修改）

---

### Step 5: LLM 客户端 ⏳

**任务清单**：
- [ ] 创建 DeepSeek LLM 客户端封装（ChatOpenAI 配置）
- [ ] 支持流式输出配置
- [ ] 支持工具绑定

**产出文件**：
- `app/ai/llm.py`
- `app/ai/__init__.py`

---

### Step 6: 系统提示词 ⏳

**任务清单**：
- [ ] 创建系统提示词模板（角色定义、能力说明、输出规范）
- [ ] 实现时间上下文注入（当前时间戳、明天 0 点、计算公式）
- [ ] 实现用户上下文注入（userId、用户名）

**产出文件**：
- `app/ai/prompts/__init__.py`
- `app/ai/prompts/system_prompt.py`

---

### Step 7: 工具实现（时间 + 用户 + 部门） ⏳

**任务清单**：
- [ ] 创建工具注册中心（registry.py，统一管理工具列表和用户上下文注入）
- [ ] 实现 parseTime（自然语言时间解析）
- [ ] 实现 getCurrentTime（返回当前时间）
- [ ] 实现 getUserByName（用户名→用户ID）
- [ ] 实现 getDepartmentTree（获取部门树）
- [ ] 实现 getDepartmentInfo（获取部门详情）

**产出文件**：
- `app/ai/tools/__init__.py`
- `app/ai/tools/registry.py`
- `app/ai/tools/time_tool.py`
- `app/ai/tools/user_tool.py`
- `app/ai/tools/department_tool.py`

---

### Step 8: 工具实现（待办 + 审批） ⏳

**任务清单**：
- [ ] 实现 createTodo（含智能用户名/ID 判断和转换）
- [ ] 实现 findTodos（按时间范围查询）
- [ ] 实现 createLeaveApproval（含 9 种假期类型 description）
- [ ] 实现 createPunchApproval
- [ ] 实现 createGoOutApproval
- [ ] 实现 findApprovals（我提交的/待我审批的）

**产出文件**：
- `app/ai/tools/todo_tool.py`
- `app/ai/tools/approval_tool.py`

---

### Step 9: 记忆管理 ⏳

**任务清单**：
- [ ] 实现 SummaryBuffer（Redis 对话缓冲读写、Token 估算、摘要触发判断）
- [ ] 实现 MemoryManager（获取记忆、添加消息、摘要生成、降级策略）
- [ ] Redis 缓存 Key 设计（ai:buffer:{id}, ai:summary:{id}）
- [ ] MongoDB 兜底（Redis 未命中时从 DB 加载）

**产出文件**：
- `app/ai/memory/__init__.py`
- `app/ai/memory/summary_buffer.py`
- `app/ai/memory/memory_manager.py`

---

### Step 10: Agent 核心 ⏳

**任务清单**：
- [ ] 实现手动 ReAct 循环（LLM 调用 → 工具执行 → 结果回传）
- [ ] 实现流式输出处理（逐 chunk 推送 ai_chunk）
- [ ] 实现工具调用拦截（推送 ai_tool_call / ai_tool_result）
- [ ] 实现循环终止条件（最终回答 或 超过最大轮次）
- [ ] 实现错误处理和 ai_error 推送

**产出文件**：
- `app/ai/agent.py`

---

### Step 11: Service 层 ⏳

**任务清单**：
- [ ] 实现 AiConversationService（创建会话、查询列表、删除会话、查询历史消息）
- [ ] 实现 AiChatService（编排 Agent + Memory + Tools + WebSocket 推送）
- [ ] WebSocket 推送方法封装（ai_chunk, ai_complete, ai_tool_call, ai_tool_result, ai_error）

**产出文件**：
- `app/services/ai_conversation_service.py`
- `app/services/ai_chat_service.py`

---

### Step 12: Router 层与集成 ⏳

**任务清单**：
- [ ] 创建 AI 会话路由（POST /v1/ai/conversation, GET /list, POST /delete, GET /{id}/messages）
- [ ] 修改 WebSocket 路由，新增 ai_chat 消息处理分支（create_task 异步派发）
- [ ] 更新 ws/message.py MessageType 枚举
- [ ] 更新 main.py 注册 AI 路由和 Beanie 模型

**产出文件**：
- `app/routers/ai.py`
- `app/routers/ws.py`（修改）
- `app/dto/ws/message.py`（修改）
- `app/main.py`（修改）

---

### Step 13: 测试 ⏳

**任务清单**：
- [ ] 工具单元测试（parseTime, createTodo, createLeaveApproval 等）
- [ ] 记忆管理单元测试（Token 估算, 摘要触发, 降级策略）
- [ ] Agent 核心循环测试（Mock LLM 响应）
- [ ] AI 会话 API 集成测试（创建/列表/删除/历史消息）
- [ ] WebSocket AI 对话集成测试（ai_chat → ai_chunk → ai_complete）

**产出文件**：
- `tests/unit/test_ai_tools.py`
- `tests/unit/test_ai_memory.py`
- `tests/unit/test_ai_agent.py`
- `tests/api/test_ai_conversation.py`
- `tests/api/test_ai_ws_chat.py`

---

## Rollback & Compatibility (回滚与兼容)

- **如何关闭**：注释掉 `main.py` 中 AI 路由注册和 Beanie 模型注册
- **如何回退**：删除 `app/ai/` 目录和新增的 model/repository/service/router 文件
- **影响面**：不影响现有功能，AI 模块完全独立

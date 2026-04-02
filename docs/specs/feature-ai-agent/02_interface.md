# API: AI Agent 对话系统接口设计

## 一、数据模型

### 1.1 AiConversation（AI 会话表）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | str | 自动 | MongoDB ObjectId |
| userId | str | 是 | 所属用户 ID |
| title | str | 否 | 会话标题（首条消息自动生成，最长 50 字符） |
| status | int | 是 | 状态：1-活跃，2-已删除 |
| createdAt | int | 是 | 创建时间戳（毫秒） |
| updatedAt | int | 是 | 最后更新时间戳（毫秒） |

**索引**：
- `userId` + `status`（复合索引，查询用户活跃会话）
- `updatedAt`（排序）

### 1.2 AiSummary（摘要表）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | str | 自动 | MongoDB ObjectId |
| conversationId | str | 是 | 关联会话 ID |
| summary | str | 是 | 摘要内容 |
| charCount | int | 是 | 摘要生成时的对话字符数 |
| createdAt | int | 是 | 首次创建时间戳（毫秒） |
| updatedAt | int | 是 | 最后更新时间戳（毫秒） |

**索引**：
- `conversationId`（唯一索引，一个会话只有一条摘要记录）

### 1.3 ChatLog（复用现有，chatType=3）

AI 对话消息复用现有 ChatLog 模型，约定：
- `chatType` = 3（AI 消息）
- `conversationId` = AiConversation.id
- `sendId` = 用户 ID（用户消息）或 `"ai"` （AI 响应）
- `recvId` = `"ai"`（用户消息）或用户 ID（AI 响应）
- `msgContent` = 消息内容
- `sendTime` = 发送时间戳（毫秒）

---

## 二、HTTP 接口

### 2.1 创建 AI 会话

- **Method**: POST
- **Path**: /v1/ai/conversation
- **Auth**: Bearer Token
- **Idempotency**: 不幂等

**Request**

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|------|------|------|------|----------|
| title | string | 否 | 会话标题 | 最大 50 字符，为空时由首条消息自动生成 |

**Response (Success)**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 会话 ID |
| userId | string | 所属用户 ID |
| title | string | 会话标题 |
| status | int | 状态 |
| createdAt | int | 创建时间戳 |
| updatedAt | int | 更新时间戳 |

### 2.2 获取会话列表

- **Method**: GET
- **Path**: /v1/ai/conversation/list
- **Auth**: Bearer Token

**Request Query**

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|------|------|------|------|----------|
| page | int | 否 | 页码 | 默认 1 |
| pageSize | int | 否 | 每页数量 | 默认 20，最大 50 |

**Response (Success)**

| 字段 | 类型 | 说明 |
|------|------|------|
| list | array | 会话列表 |
| list[].id | string | 会话 ID |
| list[].title | string | 会话标题 |
| list[].status | int | 状态 |
| list[].createdAt | int | 创建时间戳 |
| list[].updatedAt | int | 更新时间戳 |
| total | int | 总数 |

### 2.3 删除 AI 会话

- **Method**: POST
- **Path**: /v1/ai/conversation/delete
- **Auth**: Bearer Token
- **Idempotency**: 幂等

**Request**

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|------|------|------|------|----------|
| conversationId | string | 是 | 会话 ID | 非空，24 位 ObjectId |

**Response (Success)**

| 字段 | 类型 | 说明 |
|------|------|------|
| - | - | 仅返回 code=200 |

### 2.4 获取会话历史消息

- **Method**: GET
- **Path**: /v1/ai/conversation/{conversationId}/messages
- **Auth**: Bearer Token

**Request Query**

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|------|------|------|------|----------|
| page | int | 否 | 页码 | 默认 1 |
| pageSize | int | 否 | 每页数量 | 默认 20，最大 50 |

**Response (Success)**

| 字段 | 类型 | 说明 |
|------|------|------|
| list | array | 消息列表（按 sendTime 升序） |
| list[].id | string | 消息 ID |
| list[].sendId | string | 发送者 ID |
| list[].msgContent | string | 消息内容 |
| list[].sendTime | int | 发送时间戳 |
| total | int | 总数 |

### 2.5 AI 对话 SSE 流式接口

- **Method**: POST
- **Path**: /v1/ai/chat/stream
- **Auth**: Bearer Token
- **Content-Type**: application/json
- **Response Content-Type**: text/event-stream

**Request**

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|------|------|------|------|----------|
| conversationId | string | 是 | 会话 ID | 非空，24 位 ObjectId |
| content | string | 是 | 用户消息内容 | 非空，最大 4000 字符 |

**Response (SSE Event Stream)**

返回 `text/event-stream` 格式的 SSE 事件流，每个事件格式：

```
event: <event_type>
data: <json_payload>

```

**SSE 事件类型**：

| event | 说明 | data 字段 |
|-------|------|-----------|
| ai_chunk | AI 流式文本片段 | conversationId, content, index |
| ai_tool_call | 工具调用通知 | conversationId, tool, args, status |
| ai_tool_result | 工具执行结果 | conversationId, tool, result, status |
| ai_complete | AI 响应完成 | conversationId, content, messageId |
| ai_error | 错误通知 | conversationId, error, message |

**Response Headers**

| Header | 值 | 说明 |
|--------|-----|------|
| Content-Type | text/event-stream | SSE 标准格式 |
| Cache-Control | no-cache | 禁止缓存 |
| Connection | keep-alive | 保持连接 |
| X-Accel-Buffering | no | 禁止 Nginx 缓冲 |

**错误场景（SSE 事件）**

| 场景 | error | message |
|------|-------|--------|
| 会话不存在 | CONVERSATION_NOT_FOUND | 会话不存在或已删除 |
| 无权访问 | FORBIDDEN | 无权访问该会话 |
| Redis 不可用 | AI_SERVICE_ERROR | AI 服务暂时不可用，请稍后重试 |
| LLM 异常 | AI_SERVICE_ERROR | AI 处理异常: ... |
| 消息过长 | MESSAGE_TOO_LONG | 消息过长，最多 4000 字符 |

---

## 三、WebSocket 消息协议

> **注**：独立 AI 对话页面已迁移至 SSE（见 2.5 节）。WebSocket AI 消息协议仅保留给群聊 @AI 场景使用，后端内部消费 SSE 流后将事件桥接为 WS 消息推送。

### 3.1 AI 对话消息类型

在现有 WebSocket MessageType 枚举中新增以下类型：

| type | 方向 | 说明 |
|------|------|------|
| ai_chat | Client → Server | 用户发送 AI 对话消息 |
| ai_chunk | Server → Client | AI 流式响应片段 |
| ai_complete | Server → Client | AI 响应完成（含完整内容） |
| ai_tool_call | Server → Client | 工具调用通知 |
| ai_tool_result | Server → Client | 工具执行结果 |
| ai_error | Server → Client | AI 处理错误 |

### 3.2 用户发送 AI 消息 (ai_chat)

```json
{
    "type": "ai_chat",
    "conversationId": "67e1a2b3c4d5e6f7a8b9c0d1",
    "content": "帮我给张三创建一个待办，明天下午3点前完成报告"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 固定 "ai_chat" |
| conversationId | string | 是 | 会话 ID |
| content | string | 是 | 用户消息内容 |

### 3.3 AI 流式响应片段 (ai_chunk)

```json
{
    "type": "ai_chunk",
    "conversationId": "67e1a2b3c4d5e6f7a8b9c0d1",
    "content": "好的，我来帮你",
    "index": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定 "ai_chunk" |
| conversationId | string | 会话 ID |
| content | string | 本片段文本 |
| index | int | 片段序号（从 1 开始） |

### 3.4 AI 响应完成 (ai_complete)

```json
{
    "type": "ai_complete",
    "conversationId": "67e1a2b3c4d5e6f7a8b9c0d1",
    "content": "已为你创建了待办：\n标题：完成报告\n截止时间：2026-03-30 15:00\n执行人：张三\n待办ID：67e1a2b3c4d5e6f7a8b9c0d2",
    "messageId": "67e1a2b3c4d5e6f7a8b9c0d3"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定 "ai_complete" |
| conversationId | string | 会话 ID |
| content | string | 完整响应内容 |
| messageId | string | AI 响应消息的 ChatLog ID |

### 3.5 工具调用通知 (ai_tool_call)

```json
{
    "type": "ai_tool_call",
    "conversationId": "67e1a2b3c4d5e6f7a8b9c0d1",
    "tool": "parseTime",
    "args": {"expression": "明天下午3点"},
    "status": "running"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定 "ai_tool_call" |
| conversationId | string | 会话 ID |
| tool | string | 工具名称 |
| args | object | 调用参数 |
| status | string | "running" |

### 3.6 工具执行结果 (ai_tool_result)

```json
{
    "type": "ai_tool_result",
    "conversationId": "67e1a2b3c4d5e6f7a8b9c0d1",
    "tool": "parseTime",
    "result": "1743326400000 (2026-03-30 15:00:00)",
    "status": "success"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定 "ai_tool_result" |
| conversationId | string | 会话 ID |
| tool | string | 工具名称 |
| result | string | 执行结果（格式化中文） |
| status | string | "success" 或 "error" |

### 3.7 AI 错误 (ai_error)

```json
{
    "type": "ai_error",
    "conversationId": "67e1a2b3c4d5e6f7a8b9c0d1",
    "error": "AI_SERVICE_ERROR",
    "message": "AI 服务暂时不可用，请稍后重试"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定 "ai_error" |
| conversationId | string | 会话 ID |
| error | string | 错误码 |
| message | string | 错误描述 |

---

## 四、工具接口设计

### 4.1 工具注册规范

每个工具类继承 `BaseTool`，通过 LangChain `@tool` 装饰器声明：

```python
from langchain_core.tools import tool

@tool
def parseTime(expression: str) -> str:
    """将自然语言时间表达式转换为 Unix 时间戳（毫秒）。

    支持的表达式：
    - 相对日期：今天、明天、后天、大后天
    - 时间段：上午、下午、晚上、凌晨
    - 具体时间：9点、下午2点30分
    - 标准格式：2024-01-15 09:00

    Args:
        expression: 自然语言时间表达式
    """
    ...
```

**设计原则**：
- 工具的 `description`（docstring）是 LLM 决定是否调用的依据，必须清晰描述功能、参数、适用场景
- 返回格式化中文文本，LLM 可直接复用
- 需要用户上下文的工具通过闭包/工厂函数注入 `userId`

### 4.2 工具清单

#### 时间工具 (TimeParserTool)

| 工具名 | 参数 | 返回示例 |
|--------|------|---------|
| parseTime | expression: str | "1743326400000 (2026-03-30 15:00:00)" |
| getCurrentTime | 无 | "当前时间：2026-03-29 14:30:00，时间戳：1743223800000" |

#### 待办工具 (TodoTools)

| 工具名 | 参数 | 返回示例 |
|--------|------|---------|
| createTodo | title: str, desc: str = "", deadline: str = "", executorNames: list = [] | "待办创建成功！标题：完成报告，截止时间：2026-03-30 15:00，待办ID：67e1..." |
| findTodos | startTime: str = "", endTime: str = "" | "找到 3 条待办：\n1. 完成报告 - 进行中 - 截止：2026-03-30\n2. ..." |

#### 审批工具 (ApprovalTools)

| 工具名 | 参数 | 返回示例 |
|--------|------|---------|
| createLeaveApproval | leaveType: int, startTime: str, endTime: str, reason: str | "请假申请已提交！类型：病假，时间：2026-03-30 00:00 ~ 2026-03-30 23:59，审批编号：AP20260329001" |
| createPunchApproval | punchType: int, date: str, reason: str | "补卡申请已提交！类型：上班卡，日期：2026-03-28" |
| createGoOutApproval | startTime: str, endTime: str, reason: str | "外出申请已提交！时间：2026-03-29 14:00 ~ 18:00" |
| findApprovals | queryType: str | "找到 2 条审批记录：\n1. 病假申请 - 审批中 - 2026-03-28\n2. ..." |

#### 用户查询工具 (UserQueryTool)

| 工具名 | 参数 | 返回示例 |
|--------|------|---------|
| getUserByName | name: str | "找到用户：张三，用户ID：67e1a2b3c4d5e6f7a8b9c0d1" |

#### 部门查询工具 (DepartmentTools)

| 工具名 | 参数 | 返回示例 |
|--------|------|---------|
| getDepartmentTree | 无 | "部门结构：\n- 技术部 (15人)\n  - 前端组 (5人)\n  - 后端组 (10人)" |
| getDepartmentInfo | departmentId: str = "" | "部门详情：技术部，负责人：张三，人数：15，层级：1" |

---

## 五、错误码

| 错误码 | 含义 | 触发条件 |
|--------|------|----------|
| AI_SERVICE_ERROR | AI 服务异常 | DeepSeek API 调用超时或失败 |
| AI_SERVICE_UNAVAILABLE | AI 服务不可用 | API Key 未配置或服务端异常 |
| CONVERSATION_NOT_FOUND | 会话不存在 | conversationId 无效或已删除 |
| CONVERSATION_LIMIT_EXCEEDED | 会话数量超限 | 单用户会话数超过上限 |
| TOOL_EXECUTION_ERROR | 工具执行失败 | 工具调用异常 |
| MESSAGE_CONTENT_EMPTY | 消息内容为空 | content 为空或纯空格 |

---

## 六、核心流程

### 6.1 独立 AI 对话流程（SSE 模式）

```
Client                     Server                      DeepSeek API
  │                          │                              │
  │── POST /ai/chat/stream ─→│                              │
  │   {conversationId,       │                              │
  │    content}              │                              │
  │                          │── create_task ──────────────→│
  │                          │   (asyncio.Queue 中转)        │
  │                          │                              │
  │                          │   1. 获取记忆 (Redis/DB)      │
  │                          │   2. 组装上下文               │
  │                          │   3. 绑定工具                 │
  │                          │                              │
  │                          │───── chat + tools ──────────→│
  │                          │                              │
  │←─ SSE: ai_tool_call ────│←── tool_call response ──────│
  │                          │                              │
  │                          │   执行工具                    │
  │←─ SSE: ai_tool_result ──│                              │
  │                          │                              │
  │                          │───── tool result ───────────→│
  │                          │                              │
  │←─ SSE: ai_chunk ────────│←── stream chunk ────────────│
  │←─ SSE: ai_chunk ────────│←── stream chunk ────────────│
  │←─ SSE: ai_complete ─────│←── done ────────────────────│
  │                          │                              │
  │                          │   4. 保存消息到 ChatLog       │
  │                          │   5. 更新 Redis 缓冲         │
  │                          │   6. 检查 Token → 必要时摘要  │
  │                          │   7. yield sentinel → 结束流  │
```

### 6.1b 群聊 @AI 流程（WS 桥接模式）

```
Client                     Server                      DeepSeek API
  │                          │                              │
  │── WS: ai_chat ─────────→│                              │
  │                          │── create_task ──────────────→│
  │                          │   (内部消费 SSE generator)    │
  │                          │                              │
  │                          │   1. 调用 handle_ai_chat_sse │
  │                          │   2. 解析 SSE 事件           │
  │                          │   3. 添加 type 字段          │
  │                          │   4. 通过 ws_manager 推送    │
  │                          │                              │
  │←─ WS: ai_chunk ────────│                              │
  │←─ WS: ai_complete ─────│                              │
```

### 6.2 记忆管理流程

```
新消息到达
    │
    ▼
保存用户消息到 ChatLog (chatType=3)
    │
    ▼
添加到 Redis 对话缓冲 (ai:buffer:{conversationId})
    │
    ▼
估算 Token: tokenCount = (int)(charCount × 1.5)
    │
    ├── 未超限 (≤ max-token-limit) → 保持原样
    │
    └── 超限 → 调用 LLM 生成摘要
         │
         ├── 输入: 当前摘要 (ai:summary:{conversationId}) + Redis 缓冲对话
         │
         ├── 成功
         │     ├── 保存/更新 AiSummary (MongoDB)
         │     ├── 更新 Redis 摘要缓存
         │     └── 清空 Redis 对话缓冲
         │
         └── 失败
               └── 降级：Redis 缓冲只保留最近 10 条消息

获取记忆 (发送给 LLM 前)
    │
    ▼
读取摘要 (Redis → MongoDB 兜底) + 读取最近对话 (Redis → MongoDB 兜底)
    │
    ▼
返回: [摘要] + [最近 N 轮完整对话]
```

---

## 七、配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| DEEPSEEK_API_KEY | string | - | DeepSeek API 密钥 |
| DEEPSEEK_BASE_URL | string | https://api.deepseek.com | API 地址 |
| DEEPSEEK_MODEL | string | deepseek-chat | 模型名称 |
| AI_MEMORY_MAX_TOKEN_LIMIT | int | 2000 | 对话缓冲字符上限 |
| AI_MEMORY_REDIS_TTL | int | 86400 | Redis 缓存 TTL（秒，默认 24h） |
| AI_CONVERSATION_MAX_COUNT | int | 50 | 单用户最大会话数 |
| AI_TIMEOUT | int | 120 | AI 响应超时时间（秒） |
| AI_SUMMARY_MODEL | string | deepseek-chat | 摘要生成使用的模型 |

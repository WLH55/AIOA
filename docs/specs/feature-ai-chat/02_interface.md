# API: AI 消息接口（预留）

## Overview
> **注意**：本期仅做数据模型层面改动，接口设计为后续预留。

### 用户发送 AI 对话请求
- Method: POST
- Path: /v1/chat/ai
- Auth: Bearer Token
- Idempotency: 不幂等（每次请求生成新消息）

### AI 响应推送
- Method: WebSocket Push
- Channel: 群聊广播

## Request (预留)
| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|------|------|------|------|----------|
| conversationId | string | 是 | 群聊ID | 非空，群组存在校验 |
| content | string | 是 | 用户消息内容 | 非空，最大长度限制 |
| mentionAi | boolean | 是 | 是否提及AI | - |

## Response (预留)
| 字段 | 类型 | 说明 |
|------|------|------|
| messageId | string | 用户消息ID |
| status | string | 处理状态（thinking/responded） |
| aiContent | string | AI响应内容 |

## AI 消息存储结构
| 字段 | 类型 | 说明 |
|------|------|------|
| conversationId | string | 群聊ID或AI专属会话ID |
| sendId | string | 发送者ID（用户或AI标识） |
| recvId | string | 接收者ID（群聊时为空） |
| chatType | int | 固定为 3（AI消息） |
| msgContent | string | 消息内容 |
| sendTime | int | 发送时间戳 |

## Error Codes (预留)
| 错误码 | 含义 | 触发条件 |
|--------|------|----------|
| AI_SERVICE_ERROR | AI服务异常 | AI调用超时或失败 |
| INVALID_CONVERSATION | 无效会话 | 群聊不存在或用户非成员 |
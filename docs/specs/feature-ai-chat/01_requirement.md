# Feature: AI 消息类型支持

## Background (背景)
当前 chat_log 集合只支持群聊(chatType=1)和私聊(chatType=2)两种消息类型。后续需要接入 AI 对话功能，用户在群聊中可 @AI 进行交互，需要将 AI 的响应消息也持久化到 chat_log 中，以保持完整的会话历史记录。

## Goals (目标)
- 在数据模型层面新增 chatType=3 表示 AI 消息
- 为后续 AI 对话接口预留数据结构支持

## In Scope / Out of Scope (范围)

### In Scope
- ChatType 枚举新增 AI 类型
- ChatLog 模型字段描述更新
- 相关 DTO 字段描述更新
- 服务层常量定义

### Out of Scope
- AI 对话 HTTP 接口（后续单独开发）
- AI 服务集成（后续接入 AI 框架）
- WebSocket AI 消息推送逻辑

## Acceptance Criteria (验收标准)
- AC1: ChatType.AI = 3 枚举值已定义
- AC2: ChatLog.chatType 字段描述包含"3-AI消息"
- AC3: 所有相关 DTO 的 chatType 字段描述已同步更新
- AC4: chat_service.py 中定义 CHAT_TYPE_AI = 3 常量

## Constraints (约束)
- 性能要求：无额外性能影响，仅字段描述变更
- 安全要求：无
- 兼容性要求：现有 chatType=1/2 的数据不受影响

## Risks & Rollout (风险与上线)
- 风险点：无，仅枚举扩展
- 灰度策略：直接上线
- 回滚预案：删除新增枚举值即可（不影响已有数据）
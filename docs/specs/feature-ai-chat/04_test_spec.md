# Test Spec: AI 消息类型支持

## Test Scope (测试范围)
- 单元测试：枚举值验证
- 集成测试：无（本期无接口）
- 契约测试：DTO 字段描述一致性

## Test Strategy (测试策略)
- 验证 ChatType.AI 枚举值为 3
- 验证所有相关文件的 chatType 字段描述一致

## Test Cases (用例列表)
| 编号 | 场景 | 期望结果 |
|------|------|----------|
| TC1 | ChatType.AI 枚举值 | 值等于 3 |
| TC2 | ChatLog 模型 chatType 描述 | 包含"3-AI消息" |
| TC3 | DTO chatType 字段描述一致性 | 所有文件描述一致 |
| TC4 | chat_service.py 常量定义 | CHAT_TYPE_AI = 3 存在 |

## Data Preparation (数据准备)
- 前置数据：无
- Mock 依赖：无
- 时区假设：无

## Regression Impact (回归影响)
可能影响的老功能：
- 无影响（仅枚举扩展，现有群聊/私聊逻辑不变）

## Manual Verification (手动验证)
- [x] 检查 `app/models/enums/chat_type.py` 包含 `AI = 3`
- [x] 检查 `app/models/chat_log.py` 字段描述更新
- [x] 检查 `app/dto/chat_log/chat_log_request.py` 字段描述更新
- [x] 检查 `app/dto/chat_log/chat_log_response.py` 字段描述更新
- [x] 检查 `app/dto/ws/message.py` 字段描述更新
- [x] 检查 `app/services/chat_log.py` 常量定义
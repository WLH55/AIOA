# Test Spec: AI Agent 对话系统

## Test Scope (测试范围)

- 单元测试：工具层、记忆管理层、Agent 核心循环
- 集成测试：AI 会话 HTTP 接口、WebSocket AI 对话流程
- 契约测试：接口字段与 `02_interface.md` 一致性

## Test Strategy (测试策略)

- **单测覆盖**：每个工具的输入/输出、Token 估算逻辑、摘要触发条件、降级策略
- **集成测试**：会话 CRUD 端到端流程、WebSocket AI 对话完整流程
- **Mock 策略**：DeepSeek API 使用 Mock 响应，Redis/MongoDB 使用测试实例

## Test Cases (用例列表)

### 1. 工具单元测试

#### 1.1 时间工具 (TimeParserTool)

| 编号 | 场景 | 输入 | 期望结果 |
|------|------|------|----------|
| TC-1.1.1 | 解析相对日期 | "明天" | 返回明天 0 点的时间戳（毫秒） |
| TC-1.1.2 | 解析具体时间 | "明天下午3点" | 返回明天 15:00 的时间戳 |
| TC-1.1.3 | 解析标准格式 | "2026-03-30 09:00" | 返回对应时间戳 |
| TC-1.1.4 | 解析相对日期 | "后天" | 返回后天 0 点的时间戳 |
| TC-1.1.5 | 无效表达式 | "abcxyz" | 返回错误提示文本 |
| TC-1.1.6 | 获取当前时间 | 无 | 返回当前时间戳和格式化字符串 |

#### 1.2 待办工具 (TodoTools)

| 编号 | 场景 | 输入 | 期望结果 |
|------|------|------|----------|
| TC-1.2.1 | 创建待办（指定执行人ID） | title="完成报告", executorNames=["67e1..."] | 返回成功，包含标题和待办ID |
| TC-1.2.2 | 创建待办（指定用户名） | title="完成报告", executorNames=["张三"] | 自动转换用户名→ID，返回成功 |
| TC-1.2.3 | 创建待办（不指定执行人） | title="完成报告" | 默认执行人为当前用户 |
| TC-1.2.4 | 查询待办 | startTime, endTime | 返回格式化的待办列表 |
| TC-1.2.5 | 创建待办（截止时间已过） | deadline=过去时间 | 返回错误提示 |

#### 1.3 审批工具 (ApprovalTools)

| 编号 | 场景 | 输入 | 期望结果 |
|------|------|------|----------|
| TC-1.3.1 | 创建请假审批（病假） | leaveType=3, startTime, endTime, reason | 返回成功，包含审批编号 |
| TC-1.3.2 | 创建请假审批（年假） | leaveType=4, startTime, endTime, reason | 返回成功 |
| TC-1.3.3 | 创建补卡审批 | punchType=1, date, reason | 返回成功 |
| TC-1.3.4 | 创建外出审批 | startTime, endTime, reason | 返回成功 |
| TC-1.3.5 | 查询我提交的审批 | queryType="mine" | 返回审批列表 |
| TC-1.3.6 | 查询待我审批的 | queryType="pending" | 返回待审批列表 |
| TC-1.3.7 | 无效请假类型 | leaveType=99 | 返回错误提示 |

#### 1.4 用户查询工具 (UserQueryTool)

| 编号 | 场景 | 输入 | 期望结果 |
|------|------|------|----------|
| TC-1.4.1 | 按姓名查询 | name="张三" | 返回用户ID |
| TC-1.4.2 | 查询不存在的用户 | name="不存在的用户" | 返回"未找到用户"提示 |

#### 1.5 部门查询工具 (DepartmentTools)

| 编号 | 场景 | 输入 | 期望结果 |
|------|------|------|----------|
| TC-1.5.1 | 获取部门树 | 无 | 返回格式化的部门树 |
| TC-1.5.2 | 获取部门详情 | departmentId=有效ID | 返回部门详情 |
| TC-1.5.3 | 获取不存在的部门 | departmentId=无效ID | 返回错误提示 |

### 2. 记忆管理单元测试

#### 2.1 Token 估算

| 编号 | 场景 | 输入 | 期望结果 |
|------|------|------|----------|
| TC-2.1.1 | 正常中文文本 | 1000 中文字符 | tokenCount = 1500 |
| TC-2.1.2 | 空文本 | 0 字符 | tokenCount = 0 |
| TC-2.1.3 | 混合文本 | 500 混合字符 | tokenCount = 750 |

#### 2.2 摘要触发

| 编号 | 场景 | 条件 | 期望结果 |
|------|------|------|----------|
| TC-2.2.1 | 未超限 | charCount=1500, limit=2000 | 不触发摘要 |
| TC-2.2.2 | 刚好超限 | charCount=2100, limit=2000 | 触发摘要 |
| TC-2.2.3 | 远超上限 | charCount=10000, limit=2000 | 触发摘要 |

#### 2.3 摘要生成

| 编号 | 场景 | 条件 | 期望结果 |
|------|------|------|----------|
| TC-2.3.1 | 首次摘要 | 无当前摘要 + 新对话 | 生成新摘要，保存到 MongoDB 和 Redis |
| TC-2.3.2 | 增量摘要 | 有当前摘要 + 新对话 | 生成更新摘要，包含历史关键信息 |
| TC-2.3.3 | 摘要失败 | LLM 返回异常 | 降级：Redis 缓冲只保留最近 10 条 |
| TC-2.3.4 | 摘要成功后 | 缓冲已清空 | Redis buffer 为空，summary 已更新 |

#### 2.4 记忆获取

| 编号 | 场景 | 条件 | 期望结果 |
|------|------|------|----------|
| TC-2.4.1 | Redis 有缓存 | 正常情况 | 从 Redis 读取摘要 + 最近对话 |
| TC-2.4.2 | Redis 未命中 | 缓存过期 | 从 MongoDB 兜底加载 |
| TC-2.4.3 | 全新会话 | 无摘要无对话 | 返回空记忆 |

### 3. Agent 核心循环测试

| 编号 | 场景 | 条件 | 期望结果 |
|------|------|------|----------|
| TC-3.1 | 纯对话（无工具调用） | LLM 直接回答 | 推送 ai_chunk + ai_complete |
| TC-3.2 | 单次工具调用 | LLM 返回 1 个 tool_call | 推送 ai_tool_call → ai_tool_result → ai_chunk → ai_complete |
| TC-3.3 | 多次工具调用 | LLM 连续返回多个 tool_call | 按序执行，每步推送通知 |
| TC-3.4 | 工具执行失败 | 工具抛出异常 | 推送 ai_tool_result(status=error)，LLM 收到错误信息 |
| TC-3.5 | LLM 超时 | DeepSeek API 无响应 | 推送 ai_error |
| TC-3.6 | 达到最大轮次 | 工具调用超过 10 轮 | 推送 ai_complete，附带提示 |

### 4. AI 会话 API 集成测试

| 编号 | 场景 | 方法/路径 | 期望结果 |
|------|------|-----------|----------|
| TC-4.1 | 创建会话 | POST /v1/ai/conversation | 201, 返回会话信息 |
| TC-4.2 | 创建会话（自定义标题） | POST /v1/ai/conversation {title: "测试"} | 标题正确 |
| TC-4.3 | 获取会话列表 | GET /v1/ai/conversation/list | 200, 返回分页列表 |
| TC-4.4 | 删除会话 | POST /v1/ai/conversation/delete | 200 |
| TC-4.5 | 删除不存在的会话 | POST /v1/ai/conversation/delete {id: "无效"} | 返回 404 |
| TC-4.6 | 获取历史消息 | GET /v1/ai/conversation/{id}/messages | 200, 按时间升序 |
| TC-4.7 | 未认证访问 | 无 Bearer Token | 返回 401 |
| TC-4.8 | 访问他人会话 | conversationId 属于其他用户 | 返回 403 |

### 5. WebSocket AI 对话集成测试

| 编号 | 场景 | 条件 | 期望结果 |
|------|------|------|----------|
| TC-5.1 | 完整 AI 对话流程 | 发送 ai_chat → 接收响应 | 收到 ai_chunk 序列 + ai_complete |
| TC-5.2 | AI 调用工具 | 发送"帮我创建待办" | 收到 ai_tool_call + ai_tool_result + ai_complete |
| TC-5.3 | 会话不存在 | 无效 conversationId | 收到 ai_error |
| TC-5.4 | 消息内容为空 | content="" | 收到 ai_error |
| TC-5.5 | AI 处理期间正常聊天 | 发送 ai_chat 后立即发送 chat | 两者互不阻塞 |
| TC-5.6 | AI 对话不阻塞群聊 | AI 处理中发送群聊消息 | 群聊消息正常收发 |

## Data Preparation (数据准备)

### 前置数据
- 测试用户 2 个（含 JWT Token）
- 测试群组 1 个（含成员）
- 测试部门树（至少 2 级）
- DeepSeek API Mock 配置

### Mock 依赖
- `ChatOpenAI.stream()`: Mock 流式响应，模拟 tool_call 和普通回复
- `ChatOpenAI.invoke()`: Mock 摘要生成响应
- DeepSeek API Key: 使用测试 Key 或 Mock

### 时区假设
- 所有时间戳为毫秒级 Unix 时间戳
- 时间解析基于 Asia/Shanghai 时区

## Regression Impact (回归影响)

可能影响的老功能：
- **WebSocket 路由** (app/routers/ws.py)：新增 ai_chat 分支，需验证现有 chat 消息不受影响
- **ChatLog 模型**：复用 chatType=3，需验证现有 chatType=1/2 的查询不受影响
- **ws_manager**：新增辅助方法，不影响现有功能
- **main.py**：新增路由和模型注册，不影响现有路由

# Feature: AI Agent 对话系统

## Background (背景)

AIWorkHelper 已完成基础业务模块（用户认证、待办管理、审批流程、部门管理、实时聊天），用户需要通过多个独立界面分别操作这些功能。为了降低使用门槛、提升效率，需要引入 AI Agent，让用户通过自然语言即可完成系统中的各种操作，如创建待办、提交请假、查询信息等。

现有基础：
- ChatLog 模型已预留 `chatType=3`（AI 消息）
- WebSocket 连接管理器已实现，支持单播/广播
- Decision #004 已决策使用 LangChain + LangGraph
- 待办、审批、用户、部门等 CRUD 服务已完备

## Goals (目标)

- 接入 DeepSeek API，基于 LangChain 构建 AI Agent，通过 Function Calling 自主调用系统工具
- 支持独立的 AI 对话页面（ChatGPT 式体验）和群聊 @AI 触发两种入口
- 实现多会话管理，每个用户可创建多个独立的 AI 对话会话
- 实现滑动窗口 + 增量摘要的上下文管理策略，控制 Token 消耗
- 将现有业务服务注册为 Agent 工具，实现自然语言驱动业务操作
- 聊天记录和摘要持久化到 MongoDB，会话上下文缓存到 Redis

## In Scope / Out of Scope (范围)

### In Scope

#### 1. AI Agent 核心引擎
- LangChain 集成 DeepSeek API（deepseek-chat 模型）
- Function Calling 机制，Agent 自主决策调用工具和顺序
- 工具插件化设计，每个工具独立声明，新增工具简单快捷

#### 2. 对话入口（两种模式，共享引擎，解耦实现）
- **独立 AI 对话**：用户直接与 AI 对话，类似 ChatGPT 体验
- **群聊 @AI**：在群聊中通过 @AI 触发，AI 响应广播给所有群成员

#### 3. 多会话管理
- 每个用户可创建多个独立的 AI 对话会话
- 支持会话列表、新建、切换、删除
- 每个会话独立维护上下文记忆

#### 4. 工具注册（第一批，共 12 个）

**时间工具 (TimeParserTool)**
- `parseTime`：自然语言时间转 Unix 时间戳
  - 支持相对日期："今天"、"明天"、"后天"、"大后天"
  - 支持时间段："上午"、"下午"、"晚上"、"凌晨"
  - 支持具体时间："9点"、"下午2点30分"
  - 支持标准格式："2024-01-15 09:00"
- `getCurrentTime`：返回当前时间戳和格式化日期时间

**待办工具 (TodoTools)**
- `createTodo`：创建待办，支持标题、描述、截止时间、执行人
  - 智能处理：自动判断 executorNames 是用户名还是用户 ID（中文或非 24 位视为用户名，内部调用 UserService 转换）
  - 默认执行人：未指定时为当前用户
- `findTodos`：按时间范围查询待办列表，返回标题、状态、截止时间、描述

**审批工具 (ApprovalTools)**
- `createLeaveApproval`：请假审批，支持 9 种假期类型
  - 事假(1)、调休(2)、病假(3)、年假(4)、产假(5)、陪产假(6)、婚假(7)、丧假(8)、哺乳假(9)
  - 工具 description 包含枚举说明，LLM 根据用户描述自动选择类型
- `createPunchApproval`：补卡审批，支持上班卡/下班卡
- `createGoOutApproval`：外出审批，需要起止时间和原因
- `findApprovals`：查询审批记录，支持"我提交的"和"待我审批的"两种查询

**用户查询工具 (UserQueryTool)**
- `getUserByName`：用户名转用户 ID，解决用户使用人名而非 ID 的问题

**部门查询工具 (DepartmentTools)**
- `getDepartmentTree`：获取部门树结构
- `getDepartmentInfo`：获取部门详情

#### 5. 上下文记忆管理
- **滑动窗口**：保留最近几轮完整对话
- **增量摘要**：摘要累积式更新（当前摘要 + 新对话内容 → 新摘要）
- **Token 估算**：`tokenCount = (int)(charCount * 1.5)`
- **缓冲上限**：默认 2000 字符（约 3000 tokens），可通过 `ai.memory.max-token-limit` 配置
- **降级策略**：摘要生成失败时保留最近 10 条消息
- **触发时机**：仅在添加消息后检查，获取记忆为纯读取操作

#### 6. 数据持久化
- AI 对话记录复用 ChatLog 模型（chatType=3）
- 摘要持久化存储到 MongoDB
- 会话上下文缓存到 Redis，按 conversationId 隔离

#### 7. 传输方式
- 统一使用 WebSocket，通过 `type` 字段区分消息类型
- AI 流式响应通过 `asyncio.create_task` 异步派发，不阻塞正常聊天

#### 8. 性能优化
- 系统提示词注入时间上下文（当前时间戳、明天 0 点时间戳、计算公式），减少 parseTime 调用
- TodoTools 内部自动处理用户名→ID 转换，减少工具调用往返
- 工具返回格式化中文文本，LLM 直接复用，减少生成负担

### Out of Scope
- 知识库向量检索（后续迭代）
- 群聊 @AI 功能（本期仅预留入口，核心在独立对话）
- AI 对话消息的未读计数
- AI 对话的搜索功能
- 多模型切换支持

## Acceptance Criteria (验收标准)

### AC1: AI 对话核心流程
- 用户可通过 WebSocket 发送自然语言消息给 AI
- AI 通过 Function Calling 自主决策调用工具，返回正确结果
- AI 响应通过 WebSocket 流式推送（ai_chunk → ai_complete）

### AC2: 多会话管理
- 用户可创建新的 AI 对话会话
- 用户可查看会话列表
- 用户可切换不同会话，各自独立维护上下文
- 用户可删除会话及其历史记录

### AC3: 工具调用准确性
- 用户说"帮我给张三创建一个待办，明天下午3点前完成报告"
  - Agent 自动调用 getCurrentTime → parseTime → createTodo
  - 张三被正确识别为用户名并转换为用户 ID
  - 待办创建成功，返回格式化中文结果
- 用户说"我感冒了，明天请假一天"
  - Agent 自动识别为病假（leaveType=3）
  - 请假审批创建成功

### AC4: 上下文记忆
- 短期对话：完整保留最近几轮对话
- 长期上下文：摘要保留对话开始以来的关键信息
- Token 超限时自动触发摘要压缩
- 摘要生成失败时降级为保留最近 10 条消息
- 页面刷新或重新连接后，会话上下文可恢复

### AC5: 性能要求
- AI 响应流式推送，首 token 延迟 < 3 秒
- 工具调用结果实时推送（ai_tool_call / ai_tool_result）
- AI 处理通过 create_task 异步派发，不阻塞正常聊天消息收发

### AC6: 数据持久化
- AI 对话记录存储到 MongoDB（复用 ChatLog，chatType=3）
- 摘要持久化存储到 MongoDB
- 会话上下文缓存到 Redis
- 页面刷新后可恢复历史对话和摘要

## Constraints (约束)

- 性能要求：AI 响应首 token < 3s，工具调用不阻塞正常聊天
- 安全要求：AI 接口需 JWT 认证，工具调用继承当前用户权限
- 兼容性要求：复用现有 WebSocket 连接和 ChatLog 模型，不破坏已有功能
- 依赖要求：需要 DeepSeek API Key，Redis 用于会话缓存
- 成本要求：摘要压缩机制控制 Token 消耗，避免不必要的 LLM 调用

## Risks & Rollout (风险与上线)

- **风险点 1**：DeepSeek API 响应延迟或不可用
  - 缓解：设置合理的超时时间，提供友好的错误提示
- **风险点 2**：Token 估算不精确导致上下文超限
  - 缓解：使用 1.5 倍安全系数，降级策略兜底
- **风险点 3**：Function Calling 工具参数解析失败
  - 缓解：工具 description 描述清晰，包含参数说明和示例
- **风险点 4**：WebSocket 连接中断导致 AI 响应丢失
  - 缓解：AI 完整响应持久化到 ChatLog，重连后可查询
- **灰度策略**：先上线独立 AI 对话功能，群聊 @AI 后续迭代
- **回滚预案**：关闭 AI 路由注册，不影响现有功能

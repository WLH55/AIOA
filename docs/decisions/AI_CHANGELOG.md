# AI Decision Changelog

记录 AIWorkHelper 项目中的重要技术决策及其理由。

---

## 格式说明

```markdown
### [日期] Decision #编号: 决策标题
- **决策**: [做出的选择]
- **原因**: [为什么这样选择]
- **影响**: [对项目的影响]
- **替代方案**: [考虑过的其他方案]
- **文件**: [受影响的文件]
```

---

## 决策记录

### 2026-03-12 项目初始化
- **Decision**: 采用 SDD (Spec-Driven Development) 工作流
- **Reason**: 防止上下文腐烂、审查瘫痪、维护断层
- **Risk**: 需要团队适应新的文档驱动模式
- **Files**: CLAUDE.md, docs/ 目录结构

---

### 2026-03-15 Decision #001: Python 技术栈选型
- **决策**: 使用 Python 技术栈替代原 Java 方案
- **原因**: AI/LLM 生态更成熟（LangChain 原生支持 Python），开发效率更高
- **影响**: 所有业务逻辑需要用 Python 重新实现
- **替代方案**: Spring Boot + Spring AI
- **Files**: 整个项目架构

---

### 2026-03-15 Decision #002: Web 框架选择 FastAPI
- **决策**: 使用 FastAPI 作为 Web 框架
- **原因**: 原生异步支持、内置 WebSocket、自动生成 OpenAPI 文档、Pydantic 集成
- **影响**: 需要学习 FastAPI 的依赖注入系统和异步编程模型
- **替代方案**: Flask, Django
- **Files**: app/main.py, app/api/

---

### 2026-03-15 Decision #003: MongoDB ODM 选择 Beanie
- **决策**: 使用 Beanie 作为 MongoDB ODM
- **原因**: 与 FastAPI + Pydantic 深度集成、异步原生支持、减少代码重复
- **影响**: 需要遵循 Beanie 的 Document 模式，查询语法与传统 Motor 不同
- **替代方案**: Motor（直接驱动）
- **Files**: app/entity/, app/repository/

---

### 2026-03-15 Decision #004: AI 框架选择 LangChain + LangGraph
- **决策**: 使用 LangChain + LangGraph 实现 AI Agent
- **原因**: 内置支持通义千问（无需单独 dashscope）、LangGraph 状态机编排、Function Calling 支持
- **影响**: 需要学习 LangChain 概念（Chains, Agents, Tools）
- **替代方案**: 直接使用 dashscope SDK
- **Files**: app/ai/

---

### 2026-03-15 Decision #005: Redis 向量存储使用 RediSearch
- **决策**: 使用 Redis + RediSearch (RedisVL) 作为向量存储
- **原因**: 复用现有 Redis 基础设施，RediSearch 提供向量检索能力
- **影响**: 需要 Redis Stack 或启用 RediSearch 模块
- **替代方案**: Chroma, Qdrant, pgvector
- **Files**: app/config/redis.py, app/ai/tools/knowledge_tool.py

---

### 2026-03-15 Decision #006: 用户认证使用 JWT
- **决策**: 使用 JWT (HS256) 进行用户认证
- **原因**: 无状态适合分布式、实现简单、Access Token + Refresh Token 双机制
- **影响**: Token 有效期内无法主动撤销（本期不实现黑名单）
- **替代方案**: Session + Cookie
- **Files**: app/security/jwt.py, app/security/dependencies.py

---

### 2026-03-15 Decision #007: 密码哈希使用 bcrypt
- **决策**: 使用 bcrypt (work factor=12) 存储密码
- **原因**: 行业标准、安全性高、passlib 库支持
- **影响**: 哈希计算有 CPU 开销
- **替代方案**: argon2, scrypt
- **Files**: app/security/password.py

---

### 2026-03-15 Decision #008: 分层架构设计
- **决策**: 采用四层架构（接入层 → 业务层 → 数据层 → AI 层）
- **原因**: 职责清晰、符合 DDD 思想、便于扩展和测试
- **影响**: 文件数量较多，需严格遵守分层边界
- **替代方案**: 三层架构、MVC 模式
- **Files**: 整个项目结构

---

### 2026-03-15 Decision #009: 配置管理使用 Pydantic Settings
- **决策**: 使用 Pydantic Settings 管理配置
- **原因**: 类型安全、自动从环境变量读取、校验和默认值支持
- **影响**: 配置变更需要重启服务
- **替代方案**: python-dotenv 单独使用、dynaconf
- **Files**: app/config/settings.py

---

### 2026-03-15 Decision #010: 项目命名约定
- **决策**: 采用 snake_case 命名风格
- **原因**: Python 官方推荐（PEP 8），Pydantic/Beanie 最佳实践
- **影响**: API 返回的 JSON 字段名也为 snake_case，与原 Java 版本的 camelStyle 不同
- **替代方案**: camelCase（与原版保持一致）
- **Files**: 所有代码文件

---

### 2026-03-22 Decision #011: WebSocket 认证方案
- **决策**: WebSocket 连接通过 Header 传递 JWT Token 认证
- **原因**: 与 HTTP 认证一致、安全性高、实现简单
- **影响**: 需要在 WebSocket 握手阶段解析 Header
- **替代方案**: URL 参数传递（安全性较低）
- **Files**: app/api/v1/ws.py, app/service/ws_manager.py

---

### 2026-03-22 Decision #012: WebSocket 单连接限制
- **决策**: 同一用户只能有一个 WebSocket 连接，新连接踢掉旧连接
- **原因**: 避免资源浪费、简化状态管理、符合 AI 聊天场景（一对一）
- **影响**: 用户在多设备登录时会被踢下线
- **替代方案**: 多连接支持（需要更复杂的状态管理）
- **Files**: app/service/ws_manager.py

---

### 2026-03-22 Decision #013: WebSocket 心跳机制
- **决策**: 采用服务端心跳检测，30 秒间隔，60 秒超时
- **原因**: 及时发现僵尸连接、释放资源、服务端主动可控
- **影响**: 需要客户端实现 pong 响应逻辑
- **替代方案**: 客户端心跳（依赖客户端可靠性）
- **Files**: app/service/ws_manager.py

---

### 2026-03-22 Decision #014: WebSocket 消息格式
- **决策**: 使用 JSON 格式，包含 type 字段区分消息类型
- **原因**: 可读性好、调试方便、与 FastAPI 集成容易
- **影响**: 相比二进制格式有更大的消息体积
- **替代方案**: Protobuf 二进制格式（性能更高，但开发成本高）
- **Files**: app/dto/ws/message.py

---

## 实现进度记录

### 2026-03-22 HTTP 认证模块实现进度

**Spec 文档**: `docs/specs/001-auth-framework/`

| Step | 内容 | 状态 | 备注 |
|------|------|------|------|
| Step 1 | 项目初始化 | ✅ 已完成 | 之前已存在 |
| Step 2 | 配置模块 | ✅ 已完成 | 更新了 JWT/MongoDB/Redis 配置 |
| Step 3 | 数据模型 | ✅ 已完成 | `app/models/user.py` |
| Step 4 | 数据访问层 | ✅ 已完成 | `app/repository/user_repository.py` |
| Step 5 | 安全模块 | ✅ 已完成 | `app/security/` (jwt, password, dependencies) |
| Step 6 | DTO 定义 | ✅ 已完成 | `app/dto/` (auth, user, ws) |
| Step 7 | 业务逻辑层 | ✅ 已完成 | `app/services/auth_service.py` |
| Step 8 | API 路由层 | ✅ 已完成 | `app/routers/auth.py` |
| Step 9 | 中间件 | ✅ 已完成 | 更新了 ResourceNotFoundException 处理 |
| Step 10 | 应用入口 | ✅ 已完成 | `app/main.py` - 初始化 Beanie/Redis/心跳检测 |
| Step 11 | HTTP 测试 | ✅ 已完成 | `tests/` - 55 个测试用例全部通过 |
| Step 12 | WebSocket 连接管理器 | ✅ 已完成 | `app/services/ws_manager.py` |
| Step 13 | WebSocket 路由 | ✅ 已完成 | `app/routers/ws.py` |
| Step 14 | WebSocket DTO | ✅ 已完成 | `app/dto/ws/` |
| Step 15 | WebSocket 测试 | ✅ 已完成 | `tests/api/test_ws.py` - 23 个测试用例 |

**已实现的 API 端点**:
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - Token 刷新
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取当前用户信息
- `WS /api/v1/ws/chat` - WebSocket 聊天

**已实现的测试**:
- `tests/unit/test_password.py` - 密码哈希和验证测试 (11 用例)
- `tests/unit/test_jwt.py` - JWT 编解码测试 (21 用例)
- `tests/api/test_auth.py` - 认证接口集成测试 (23 用例)
- `tests/api/test_ws.py` - WebSocket 测试 (23 用例)
- **总计**: 78 个测试用例全部通过

**WebSocket 功能**:
- 连接注册与注销
- 单用户单连接限制（踢掉旧连接）
- 心跳检测（30s 间隔，60s 超时）
- 消息广播
- Token 认证

**实施完成**: 2026-03-23

---

## 待决策项

以下问题需要在后续迭代中决策：

- [ ] RBAC 权限控制设计方案
- [ ] 多租户数据隔离策略
- [ ] Token 黑名单实现（是否需要）
- [ ] 第三方 OAuth 登录（钉钉/企业微信）
- [ ] 文件存储方案（本地/OSS/S3）
- [ ] 日志系统（结构化日志、日志收集）
- [ ] 监控和告警方案
- [ ] 部署方案（Docker/K8s）
- [ ] WebSocket 多实例部署（是否需要 Redis Pub/Sub）
- [ ] WebSocket 消息持久化（是否需要）

---

## 2026-03-24 CRUD 业务接口实现

### Decision #015: Java 到 Python 架构映射
- **决策**: 采用三层架构映射（Router → Service → Repository）
- **原因**: 与现有项目结构保持一致，降低学习成本
- **影响**: 无接口层，略降低可测试性（可接受）
- **替代方案**: 引入抽象基类（增加复杂度，收益不大）
- **Files**: app/routers/, app/services/, app/repository/

---

### Decision #016: 时间戳单位统一
- **决策**: 统一使用毫秒级 Unix 时间戳
- **原因**: Python 项目已有实现使用毫秒级，精度更高，适用于高并发场景
- **影响**: 与 Java 版本（秒级）交互时需注意转换（×1000）
- **替代方案**: 使用秒级（与 Java 一致，但精度降低）
- **Files**: 所有 entity 和 DTO 文件

---

### Decision #017: 审批流程设计
- **决策**: 审批流程根据部门层级自动确定审批人
- **原因**: 与 Java 版本保持一致，符合企业审批流程常见设计
- **影响**: 实现复杂度较高，需要解析部门 parentPath
- **替代方案**: 手动指定审批人（灵活性高，但用户操作繁琐）
- **Files**: app/services/approval_service.py

---

### Decision #018: 部门用户级联操作
- **决策**: 添加/删除部门用户时自动级联到上级部门
- **原因**: 简化用户管理，保证上级部门能看到所有下级部门成员
- **影响**: 操作可能影响多条记录，需要注意事务一致性
- **替代方案**: 不级联（用户管理更灵活，但操作繁琐）
- **Files**: app/services/department_service.py

---

### Decision #019: 待办删除权限
- **决策**: 仅创建人可删除待办事项
- **原因**: 防止误删他人待办，与 Java 版本保持一致
- **影响**: 管理员也无法删除（可通过修改数据库解决）
- **替代方案**: 管理员可删除任意待办（需要额外的权限判断）
- **Files**: app/services/todo_service.py

---

### 实现进度记录

**Spec 文档**: `docs/specs/crud-implementation/`

| Step | 内容 | 状态 | 备注 |
|------|------|------|------|
| Step 1 | User DTO 层 | ✅ 已完成 | user_request.py, user_response.py |
| Step 2 | User Repository 层 | ✅ 已完成 | 扩展 user_repository.py |
| Step 3 | User Service 层 | ✅ 已完成 | user_service.py |
| Step 4 | User Router 层 | ✅ 已完成 | user.py |
| Step 5 | Todo DTO 层 | ✅ 已完成 | todo_request.py, todo_response.py |
| Step 6 | Todo Repository 层 | ✅ 已完成 | todo_repository.py |
| Step 7 | Todo Service 层 | ✅ 已完成 | todo_service.py |
| Step 8 | Todo Router 层 | ✅ 已完成 | todo.py |
| Step 9 | Approval DTO 层 | ✅ 已完成 | approval_request.py, approval_response.py |
| Step 10 | Approval Repository 层 | ✅ 已完成 | approval_repository.py |
| Step 11 | Approval Service 层 | ✅ 已完成 | approval_service.py |
| Step 12 | Approval Router 层 | ✅ 已完成 | approval.py |
| Step 13 | Department DTO 层 | ✅ 已完成 | department_request.py, department_response.py |
| Step 14 | Department Repository 层 | ✅ 已完成 | department_repository.py, department_user_repository.py |
| Step 15 | Department Service 层 | ✅ 已完成 | department_service.py |
| Step 16 | Department Router 层 | ✅ 已完成 | department.py |
| Step 17 | ChatLog DTO 层 | ✅ 已完成 | chat_log_request.py, chat_log_response.py |
| Step 18 | ChatLog Repository 层 | ✅ 已完成 | chat_log_repository.py |
| Step 19 | ChatLog Service 层 | ✅ 已完成 | chat_log_service.py |
| Step 20 | ChatLog Router 层 | ✅ 已完成 | chat_log.py |
| Step 21 | 注册路由 | ✅ 已完成 | main.py 更新 |
| Step 22 | 代码审查 | ✅ 已完成 | 发现 6 个问题并修复 |

**代码审查修复 (2026-03-24)**:

| 问题 | 修复 |
|------|------|
| 权限校验缺失 | 用户编辑/删除接口添加管理员权限验证 |
| 待办完成漏洞 | 验证只能完成自己的待办 |
| 用户创建默认禁用 | 修改默认 status=0 |
| 审批完成时间缺失 | 通过时设置 finishAt 等字段 |
| 审批编号可能重复 | 使用时间戳+随机数生成 |
| 部门用户缺少索引 | 添加 depId/userId 索引 |

**已实现的 API 端点（31 个）**:

User 模块 (7 个):
- `POST /api/v1/user/login` - 用户登录
- `GET /api/v1/user/{user_id}` - 获取用户信息
- `POST /api/v1/user` - 创建用户
- `PUT /api/v1/user` - 编辑用户
- `DELETE /api/v1/user/{user_id}` - 删除用户
- `GET /api/v1/user/list` - 用户列表
- `POST /api/v1/user/password` - 修改密码

Todo 模块 (7 个):
- `GET /api/v1/todo/{todo_id}` - 获取待办详情
- `POST /api/v1/todo` - 创建待办
- `PUT /api/v1/todo` - 编辑待办
- `DELETE /api/v1/todo/{todo_id}` - 删除待办
- `POST /api/v1/todo/finish` - 完成待办
- `POST /api/v1/todo/record` - 创建操作记录
- `GET /api/v1/todo/list` - 待办列表

Approval 模块 (4 个):
- `GET /api/v1/approval/{approval_id}` - 获取审批详情
- `POST /api/v1/approval` - 创建审批申请
- `PUT /api/v1/approval/dispose` - 处理审批
- `GET /api/v1/approval/list` - 审批列表

Department 模块 (9 个):
- `GET /api/v1/dep/soa` - 获取部门树结构
- `GET /api/v1/dep/{department_id}` - 获取部门详情
- `POST /api/v1/dep` - 创建部门
- `PUT /api/v1/dep` - 更新部门
- `DELETE /api/v1/dep/{department_id}` - 删除部门
- `POST /api/v1/dep/user` - 设置部门用户
- `POST /api/v1/dep/user/add` - 添加部门员工
- `DELETE /api/v1/dep/user/remove` - 删除部门员工
- `GET /api/v1/dep/user/{user_id}` - 获取用户部门信息

ChatLog 模块 (4 个):
- `GET /api/v1/chat/{chat_log_id}` - 获取聊天记录详情
- `POST /api/v1/chat` - 创建聊天记录
- `GET /api/v1/chat/list` - 聊天记录列表
- `GET /api/v1/chat/conversation/{conversation_id}` - 按会话查询

**实施完成**: 2026-03-24

---

## 2026-03-25 群组功能实现 (Group Feature)

### Decision #020: 群组功能架构设计
- **决策**: 创建独立的 Group 模型，复用 ChatLog 处理群组消息
- **原因**: 解耦群组管理和消息存储，ChatLog 已支持群聊（chatType=1）
- **影响**: 新增 Group 模型和相关 CRUD 接口，WebSocket 系统消息支持
- **替代方案**: 将群组信息嵌入 ChatLog（不符合关系型设计原则）
- **Files**: app/models/group.py, app/services/group_service.py

---

### Decision #021: 群组成员管理权限
- **决策**: 仅群主可执行管理操作（邀请/移除成员、修改群组、解散群组）
- **原因**: 简化权限模型，符合企业内部群组常见设计
- **影响**: 群主退出需要先解散或转让（本期不支持转让）
- **替代方案**: 引入管理员角色（增加复杂度）
- **Files**: app/services/group_service.py

---

### Decision #022: 群组系统消息通知
- **决策**: 使用 WebSocket 广播系统消息 + ChatLog 持久化
- **原因**: 实时通知所有成员，同时保留消息历史
- **影响**: 需要确保所有成员在线才能收到实时通知
- **替代方案**: 仅持久化，用户轮询查询（实时性差）
- **Files**: app/services/group_service.py (_send_system_message)

---

### 实现进度记录

**Spec 文档**: `docs/specs/feature-group/`

| Step | 内容 | 状态 | 备注 |
|------|------|------|------|
| Step 1 | Group 数据模型 | ✅ 已完成 | app/models/group.py |
| Step 2 | 请求 DTO | ✅ 已完成 | app/dto/group/group_request.py |
| Step 3 | 响应 DTO | ✅ 已完成 | app/dto/group/group_response.py |
| Step 4 | Repository 层 | ✅ 已完成 | app/repository/group_repository.py |
| Step 5 | Service 层 | ✅ 已完成 | app/services/group_service.py |
| Step 6 | Router 层 | ✅ 已完成 | app/routers/group.py |
| Step 7 | 注册路由和模型 | ✅ 已完成 | app/main.py 更新 |

**已实现的 API 端点（8 个）**:

Group 模块:
- `POST /api/v1/group/create` - 创建群组
- `GET /api/v1/group/list` - 获取群组列表
- `GET /api/v1/group/{id}` - 获取群组详情
- `POST /api/v1/group/{id}/invite` - 邀请成员
- `POST /api/v1/group/{id}/remove` - 移除成员
- `POST /api/v1/group/{id}/exit` - 退出群组
- `PUT /api/v1/group/{id}` - 修改群组信息
- `DELETE /api/v1/group/{id}` - 解散群组

**WebSocket 系统消息类型**:
- `group_create` - 群组创建通知
- `group_dismiss` - 群组解散通知
- `group_invite` - 成员邀请通知
- `group_remove` - 成员移除通知
- `group_exit` - 成员退出通知

**常量定义**:
- `MAX_MEMBERS = 100` - 群组成员上限
- `STATUS_NORMAL = 1` - 正常状态
- `STATUS_DISMISSED = 2` - 已解散状态

**业务规则**:
1. 创建群组时，创建者自动成为群主
2. 成员数量上限 100 人
3. 只有群主可以邀请/移除成员、修改群组、解散群组
4. 群主不能退出群组（需先解散）
5. 解散后群组状态更新为已解散，但数据保留

**实施完成**: 2026-03-25

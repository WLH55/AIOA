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
| Step 6 | DTO 定义 | ✅ 已完成 | `app/dto/` (auth, user) |
| Step 7 | 业务逻辑层 | ✅ 已完成 | `app/services/auth_service.py` |
| Step 8 | API 路由层 | ✅ 已完成 | `app/routers/auth.py` |
| Step 9 | 中间件 | ✅ 已完成 | 更新了 ResourceNotFoundException 处理 |
| Step 10 | 应用入口 | ✅ 已完成 | `app/main.py` - 初始化 Beanie/Redis |
| Step 11 | 测试 | ❌ 待实现 | `tests/` |
| Step 12 | WebSocket 连接管理器 | ❌ 待实现 | `app/services/ws_manager.py` |
| Step 13 | WebSocket 路由 | ❌ 待实现 | `app/routers/ws.py` |
| Step 14 | WebSocket DTO | ❌ 待实现 | `app/dto/ws/` |
| Step 15 | WebSocket 测试 | ❌ 待实现 | `tests/api/test_ws.py` |

**已实现的 API 端点**:
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - Token 刷新
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取当前用户信息

**下一步**: 实现 WebSocket 模块 (Step 12-15)

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

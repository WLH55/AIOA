# Feature: 项目框架与用户认证模块

## Background (背景)

AIWorkHelper 是一款专为企业办公场景打造的 AI 智能助手系统。系统通过集成阿里云通义千问大模型，实现自然语言驱动的交互体验。

作为系统的基础设施，需要首先搭建：
1. **项目框架**：基于 FastAPI 的分层架构，支持后续业务模块扩展
2. **用户认证模块**：提供用户注册、登录、Token 管理能力，是所有业务功能的基石

## Goals (目标)

### 项目框架目标
- 建立清晰的分层架构（接入层 → 业务层 → 数据层 → AI 层）
- 配置 MongoDB + Redis 数据存储
- 集成 LangChain + LangGraph AI 框架
- 提供统一的配置管理和日志系统

### 认证模块目标
- 支持用户注册（用户名/邮箱）
- 支持用户登录（返回 JWT Token）
- 支持 Token 刷新机制
- 提供用户信息查询接口

## In Scope / Out of Scope (范围)

### In Scope

#### 项目框架
- [x] FastAPI 项目结构搭建
- [x] MongoDB 连接配置（使用 Beanie ODM）
- [x] Redis 连接配置
- [x] 配置管理（环境变量 + Pydantic Settings）
- [x] 全局异常处理
- [x] 请求日志中间件
- [x] WebSocket 基础配置

#### 用户认证
- [x] 用户注册（用户名 + 邮箱 + 密码）
- [x] 用户登录（支持用户名或邮箱登录）
- [x] JWT Access Token 生成（有效期 7 天）
- [x] JWT Refresh Token 生成（有效期 30 天）
- [x] Token 刷新接口
- [x] 获取当前用户信息接口
- [x] 密码哈希存储（bcrypt）
- [x] 基础字段校验

### Out of Scope

#### 本期不做的功能
- [ ] 手机号 + 验证码登录
- [ ] 第三方 OAuth 登录（钉钉/企业微信）
- [ ] RBAC 权限控制（角色管理、权限校验）
- [ ] Token 黑名单机制（强制注销）
- [ ] 多租户数据隔离
- [ ] 部门管理
- [ ] 用户信息修改
- [ ] 密码重置（忘记密码）
- [ ] 邮箱验证流程

#### AI 功能（后续模块）
- [ ] LangChain Agent 实现
- [ ] Function Calling 工具
- [ ] 待办业务逻辑
- [ ] 审批业务逻辑
- [ ] 知识库向量检索

## Acceptance Criteria (验收标准)

### AC1: 项目框架可正常启动
```bash
# 期望结果
$ uvicorn app.main:app --reload
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### AC2: MongoDB 连接成功
- 启动时自动连接 MongoDB
- Beanie 初始化所有 Entity
- 连接失败时应用拒绝启动

### AC3: Redis 连接成功
- 启动时验证 Redis 可用性
- 支持 PING 操作

### AC4: 用户注册功能
```bash
# 请求
POST /api/v1/auth/register
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "Password123",
  "full_name": "测试用户",
  "employee_id": "E001"
}

# 期望响应 201
{
  "user_id": "507f1f77bcf86cd799439011",
  "username": "testuser",
  "email": "test@example.com"
}
```

### AC5: 用户登录功能
```bash
# 请求
POST /api/v1/auth/login
{
  "username": "testuser",
  "password": "Password123"
}

# 期望响应 200
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "user_id": "...",
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

### AC6: Token 认证保护
```bash
# 无 Token 访问受保护接口
GET /api/v1/auth/me
# 期望响应 401
{
  "detail": "Not authenticated"
}

# 带 Token 访问
GET /api/v1/auth/me
Authorization: Bearer eyJhbGci...
# 期望响应 200，返回用户信息
```

### AC7: Token 刷新功能
```bash
# 请求
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJhbGci..."
}

# 期望响应 200，返回新的 access_token
```

### AC8: 重复注册被拒绝
```bash
# 使用已存在的用户名注册
POST /api/v1/auth/register
{
  "username": "testuser",  # 已存在
  "email": "new@example.com",
  "password": "Password123"
}

# 期望响应 400
{
  "detail": "Username already exists"
}
```

### AC9: 密码安全性
- 密码以 bcrypt 哈希存储，不存储明文
- 数据库中 password_hash 字段格式：$2b$12$...
- 登录时使用相同的哈希算法验证

### AC10: 数据校验
```bash
# 弱密码被拒绝
POST /api/v1/auth/register
{
  "username": "test",
  "email": "test@example.com",
  "password": "123456"  # 弱密码
}

# 期望响应 422
{
  "detail": "Password must be at least 8 characters"
}
```

### AC11: API 文档自动生成
- 访问 http://localhost:8000/docs 显示 Swagger UI
- 访问 http://localhost:8000/redoc 显示 ReDoc
- 所有接口包含完整的 Request/Response 示例

## Constraints (约束)

### 性能要求
- 登录接口响应时间 < 500ms
- Token 验证中间件延迟 < 50ms

### 安全要求
- 密码最小长度 8 位，必须包含字母和数字
- JWT 使用 HS256 算法签名
- 密码哈希使用 bcrypt，work factor = 12
- 敏感信息（密码、Token）不在日志中输出

### 兼容性要求
- Python 版本：>= 3.11
- MongoDB 版本：>= 6.0
- Redis 版本：>= 7.0（支持 RediSearch）

### 配置要求
- 所有配置通过环境变量管理
- `.env.example` 提供配置模板
- 敏感配置不提交到 Git

## Risks & Rollout (风险与上线)

### 风险点

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| MongoDB 连接失败导致启动失败 | 高 | 启动时健康检查，失败则拒绝启动 |
| Redis 不可用影响后续功能 | 中 | 记录警告日志，降级为非缓存模式 |
| JWT 密钥泄露导致安全漏洞 | 高 | 密钥从环境变量读取，定期轮换 |
| bcrypt 性能开销 | 低 | work factor 设为 12 平衡安全与性能 |

### 数据迁移
- 本期为新系统，无需数据迁移
- MongoDB 集合创建由 Beanie 自动处理

### 回滚预案
- 代码通过 Git 管理，可随时回滚
- 数据库变更使用 Beanie 迁移机制

## Dependencies (依赖)

### 内部依赖
- 无（这是基础模块，其他模块依赖此模块）

### 外部依赖
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
motor>=3.6.0
beanie>=1.27.0
redis>=5.2.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pydantic[email]>=2.10.0
pydantic-settings>=2.6.0
python-dotenv>=1.0.0
```

## Success Metrics (成功指标)

- [ ] 项目可正常启动，服务监听在 8000 端口
- [ ] 可通过 Swagger UI 访问 API 文档
- [ ] 用户注册流程完整可用
- [ ] 用户登录流程完整可用
- [ ] Token 认证保护有效
- [ ] 所有单元测试通过
- [ ] 代码通过类型检查 (mypy)
- [ ] SDD 文档完整归档

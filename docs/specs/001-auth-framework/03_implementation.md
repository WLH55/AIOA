# Implementation: 项目框架与用户认证模块

## Objective (目标复述)

搭建 AIWorkHelper 项目基础框架，实现用户注册、登录、Token 管理功能。采用 FastAPI + Beanie + MongoDB + Redis 技术栈，建立清晰的分层架构，为后续业务模块和 AI 功能奠定基础。

---

## File Changes (变更范围)

### 新增文件结构

```
aiworkhelper/
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI 应用入口
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                    # 依赖注入（get_current_user）
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py                # 认证路由
│   │       ├── ws.py                  # WebSocket 路由
│   │       └── router.py              # 路由聚合
│   │
│   ├── service/
│   │   ├── __init__.py
│   │   ├── auth_service.py            # 认证业务逻辑
│   │   ├── user_service.py            # 用户业务逻辑
│   │   └── ws_manager.py              # WebSocket 连接管理器
│   │
│   ├── repository/
│   │   ├── __init__.py
│   │   └── user_repository.py         # 用户数据访问
│   │
│   ├── entity/
│   │   ├── __init__.py
│   │   └── user.py                    # User Document
│   │
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── register.py            # 注册 DTO
│   │   │   ├── login.py               # 登录 DTO
│   │   │   └── token.py               # Token DTO
│   │   ├── ws/
│   │   │   ├── __init__.py
│   │   │   ├── message.py             # WebSocket 消息 DTO
│   │   │   └── response.py            # WebSocket 响应 DTO
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   └── user_response.py       # 用户响应 DTO
│   │   └── common/
│   │       ├── __init__.py
│   │       └── response.py            # 通用响应结构
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── jwt.py                     # JWT 编解码
│   │   ├── password.py                # 密码哈希
│   │   └── dependencies.py            # 认证依赖
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                # 应用配置
│   │
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py           # 全局异常处理
│
├── docs/
│   └── specs/001-auth-framework/      # SDD 文档
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # pytest 配置
│   └── api/
│       ├── test_auth.py               # 认证接口测试
│       └── test_ws.py                 # WebSocket 测试
│
├── .env.example                       # 环境变量模板
├── .gitignore
├── requirements.txt                   # 依赖列表
├── pyproject.toml                     # 项目配置
└── README.md
```

---

## Data Changes (数据变更)

### MongoDB 集合

#### users 集合

```javascript
// 由 Beanie 自动创建，索引定义如下
db.users.createIndex({ username: 1 }, { unique: true })
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ employee_id: 1 })
db.users.createIndex({ status: 1 })
```

### Redis 数据结构

本期仅连接 Redis，无特定数据结构。后续用于：
- Session 缓存
- 向量索引（RediSearch）

---

## Core Logic (核心流程)

### 1. 用户注册流程

```
┌─────────────────────────────────────────────────────────────────┐
│  用户注册                                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 接收请求                                                    │
│     POST /api/v1/auth/register                                  │
│     ↓                                                           │
│  2. Pydantic 校验                                              │
│     - username 格式（3-50字符，字母数字下划线）                  │
│     - email 格式                                                │
│     - password 强度（最小8位，字母+数字）                        │
│     ↓                                                           │
│  3. 检查用户名是否已存在                                        │
│     user_repository.find_by_username()                          │
│     ↓                                                           │
│  4. 检查邮箱是否已存在                                          │
│     user_repository.find_by_email()                             │
│     ↓                                                           │
│  5. 密码哈希                                                    │
│     password_hash = hash_password(password)  # bcrypt           │
│     ↓                                                           │
│  6. 创建用户记录                                                │
│     user = User(username, email, password_hash, ...)            │
│     ↓                                                           │
│  7. 保存到 MongoDB                                              │
│     await user.save()                                           │
│     ↓                                                           │
│  8. 返回用户信息（不含密码）                                    │
│     return UserResponse(user_id, username, email)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 用户登录流程

```
┌─────────────────────────────────────────────────────────────────┐
│  用户登录                                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 接收请求                                                    │
│     POST /api/v1/auth/login                                     │
│     ↓                                                           │
│  2. 查找用户                                                    │
│     # 支持用户名或邮箱登录                                       │
│     user = find_by_username_or_email(username/email)            │
│     ↓                                                           │
│  3. 验证用户存在                                                │
│     if not user: raise INVALID_CREDENTIALS                      │
│     ↓                                                           │
│  4. 验证用户状态                                                │
│     if user.status != "active": raise USER_INACTIVE             │
│     ↓                                                           │
│  5. 验证密码                                                    │
│     if not verify_password(password, user.password_hash):       │
│         raise INVALID_CREDENTIALS                               │
│     ↓                                                           │
│  6. 更新最后登录时间                                            │
│     user.last_login_at = datetime.utcnow()                       │
│     await user.save()                                           │
│     ↓                                                           │
│  7. 生成 Token                                                  │
│     access_token = create_access_token(user)                     │
│     refresh_token = create_refresh_token(user)                   │
│     ↓                                                           │
│  8. 返回 Token 和用户信息                                       │
│     return LoginResponse(access_token, refresh_token, user)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Token 认证流程（依赖注入）

```
┌─────────────────────────────────────────────────────────────────┐
│  Token 认证                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 从 Header 提取 Token                                        │
│     Authorization: Bearer {token}                               │
│     ↓                                                           │
│  2. 解码 JWT                                                    │
│     payload = decode_jwt(token)                                 │
│     ↓                                                           │
│  3. 验证 Token 类型                                             │
│     if payload["type"] != "access": raise INVALID_TOKEN_TYPE   │
│     ↓                                                           │
│  4. 验证 Token 未过期                                           │
│     if payload["exp"] < now(): raise EXPIRED_TOKEN              │
│     ↓                                                           │
│  5. 提取用户 ID                                                 │
│     user_id = payload["sub"]                                    │
│     ↓                                                           │
│  6. 查询用户                                                    │
│     user = user_repository.find_by_id(user_id)                  │
│     ↓                                                           │
│  7. 验证用户存在且活跃                                          │
│     if not user or user.status != "active":                     │
│         raise USER_NOT_FOUND                                    │
│     ↓                                                           │
│  8. 返回用户对象                                                │
│     return user                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Token 刷新流程

```
┌─────────────────────────────────────────────────────────────────┐
│  Token 刷新                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 接收 refresh_token                                          │
│     POST /api/v1/auth/refresh                                   │
│     ↓                                                           │
│  2. 解码 JWT                                                    │
│     payload = decode_jwt(refresh_token)                         │
│     ↓                                                           │
│  3. 验证 Token 类型                                             │
│     if payload["type"] != "refresh":                            │
│         raise INVALID_TOKEN_TYPE                                │
│     ↓                                                           │
│  4. 验证 Token 未过期                                           │
│     if payload["exp"] < now(): raise EXPIRED_TOKEN              │
│     ↓                                                           │
│  5. 提取用户 ID                                                 │
│     user_id = payload["sub"]                                    │
│     ↓                                                           │
│  6. 查询用户                                                    │
│     user = user_repository.find_by_id(user_id)                  │
│     ↓                                                           │
│  7. 验证用户存在且活跃                                          │
│     if not user or user.status != "active":                     │
│         raise INVALID_TOKEN                                     │
│     ↓                                                           │
│  8. 生成新的 Access Token                                       │
│     new_access_token = create_access_token(user)                │
│     ↓                                                           │
│  9. 返回新 Token                                                │
│     return RefreshResponse(new_access_token)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5. WebSocket 连接认证流程

```
┌─────────────────────────────────────────────────────────────────┐
│  WebSocket 连接认证                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 客户端发起 WebSocket 连接                                    │
│     ws://host/api/v1/ws/chat                                    │
│     Header: Authorization: Bearer {access_token}               │
│     ↓                                                           │
│  2. 从 Header 提取 Token                                        │
│     token = extract_bearer_token(authorization_header)          │
│     ↓                                                           │
│  3. 验证 Token                                                  │
│     payload = decode_jwt(token)                                 │
│     if invalid: close connection with code 4002                 │
│     if expired: close connection with code 4003                 │
│     ↓                                                           │
│  4. 提取用户信息                                                │
│     user_id = payload["sub"]                                    │
│     user = user_repository.find_by_id(user_id)                  │
│     if not user: close connection with code 4004               │
│     ↓                                                           │
│  5. 检查是否已有连接（单连接限制）                               │
│     if user_id in active_connections:                           │
│         old_ws = active_connections[user_id]                    │
│         await old_ws.send_json({"type": "kicked", ...})        │
│         await old_ws.close()                                    │
│     ↓                                                           │
│  6. 建立映射                                                    │
│     session_id = generate_session_id()                          │
│     session_to_user[session_id] = user_id                       │
│     user_to_ws[user_id] = websocket                             │
│     ws_to_session[websocket] = session_id                       │
│     ↓                                                           │
│  7. 发送连接成功消息                                            │
│     await websocket.send_json({                                 │
│         "type": "connected",                                    │
│         "user_id": user_id,                                     │
│         "username": user.username,                              │
│         "session_id": session_id                                │
│     })                                                          │
│     ↓                                                           │
│  8. 启动心跳检测任务                                            │
│     start_heartbeat_task(websocket, session_id)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6. WebSocket 消息处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│  WebSocket 消息处理                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 接收消息                                                    │
│     message = await websocket.receive_json()                    │
│     ↓                                                           │
│  2. 解析消息类型                                                │
│     msg_type = message.get("type")                              │
│     ↓                                                           │
│  3. 根据类型分发处理                                            │
│     switch msg_type:                                            │
│       case "chat":    → handle_chat_message()                   │
│       case "pong":    → handle_pong()                           │
│       case "close":   → handle_close()                          │
│       default:        → send_error("unknown message type")      │
│     ↓                                                           │
│  4. 聊天消息处理                                                │
│     - 获取用户 ID（从 session_to_user）                         │
│     - 调用 AI 服务处理消息                                      │
│     - 流式返回响应                                              │
│     ↓                                                           │
│  5. 心跳响应处理                                                │
│     - 更新最后活跃时间                                          │
│     - 重置心跳超时计时器                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7. WebSocket 心跳检测流程

```
┌─────────────────────────────────────────────────────────────────┐
│  WebSocket 心跳检测                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 服务端定时任务（每 30 秒）                                   │
│     for each active_websocket:                                  │
│         await websocket.send_json({"type": "ping"})            │
│         last_ping_time[session_id] = now()                     │
│     ↓                                                           │
│  2. 检测超时（每 60 秒）                                        │
│     for each session in last_ping_time:                         │
│         if now() - last_ping_time[session] > 60s:              │
│             await close_connection(session)                    │
│             cleanup_session(session)                            │
│     ↓                                                           │
│  3. 客户端响应                                                  │
│     收到 {"type": "ping"} 后                                    │
│     发送 {"type": "pong"}                                       │
│     ↓                                                           │
│  4. 更新活跃时间                                                │
│     last_pong_time[session_id] = now()                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8. WebSocket 连接关闭流程

```
┌─────────────────────────────────────────────────────────────────┐
│  WebSocket 连接关闭                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 检测关闭事件                                                │
│     - 客户端主动关闭                                            │
│     - 心跳超时                                                  │
│     - 服务端异常                                                │
│     ↓                                                           │
│  2. 获取 Session ID                                             │
│     session_id = ws_to_session[websocket]                       │
│     ↓                                                           │
│  3. 清理映射                                                    │
│     user_id = session_to_user.pop(session_id)                   │
│     user_to_ws.pop(user_id, None)                               │
│     ws_to_session.pop(websocket, None)                          │
│     last_ping_time.pop(session_id, None)                        │
│     ↓                                                           │
│  4. 记录日志                                                    │
│     logger.info(f"WebSocket closed: user={user_id}, ...")      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Validations (关键校验)

### 输入校验（Pydantic）

| 字段 | 校验规则 |
|-----|---------|
| username | 长度 3-50，只允许字母、数字、下划线 |
| email | 有效邮箱格式 |
| password | 最小 8 位，必须包含至少一个字母和一个数字 |
| phone | 符合手机号格式（可选）|

### 业务校验

| 场景 | 校验逻辑 |
|-----|---------|
| 注册 | 用户名不能重复 |
| 注册 | 邮箱不能重复 |
| 登录 | 用户必须存在 |
| 登录 | 密码必须正确 |
| 登录 | 用户状态必须为 active |
| Token 验证 | Token 必须有效且未过期 |
| Token 验证 | 用户必须存在且活跃 |

### 密码安全

```python
# 哈希算法：bcrypt
# Work factor：12
# 生成密码哈希
password_hash = bcrypt.hash(password, rounds=12)

# 验证密码
is_valid = bcrypt.verify(password, password_hash)
```

### JWT 配置

```python
# 算法：HS256
# 密钥：从环境变量 SECRET_KEY 读取
# Access Token 有效期：7 天
# Refresh Token 有效期：30 天
```

---

## Execution Plan (分步计划)

### Step 1: 项目初始化

**任务**：
- 创建项目目录结构
- 生成 requirements.txt
- 生成 pyproject.toml
- 生成 .env.example
- 生成 .gitignore

**文件**：
- `requirements.txt`
- `pyproject.toml`
- `.env.example`
- `.gitignore`

---

### Step 2: 配置模块

**任务**：
- 创建 Settings 类（Pydantic Settings）
- 定义环境变量
- MongoDB 连接配置
- Redis 连接配置
- JWT 配置

**文件**：
- `app/config/__init__.py`
- `app/config/settings.py`

---

### Step 3: 数据模型

**任务**：
- 定义 User Document（Beanie）
- 定义索引
- 定义字段类型和校验

**文件**：
- `app/entity/__init__.py`
- `app/entity/user.py`

---

### Step 4: 数据访问层

**任务**：
- 创建 UserRepository
- 实现 CRUD 方法
- 实现按用户名/邮箱查询

**文件**：
- `app/repository/__init__.py`
- `app/repository/user_repository.py`

---

### Step 5: 安全模块

**任务**：
- 实现 JWT 编解码
- 实现密码哈希和验证
- 实现 get_current_user 依赖

**文件**：
- `app/security/__init__.py`
- `app/security/jwt.py`
- `app/security/password.py`
- `app/security/dependencies.py`

---

### Step 6: DTO 定义

**任务**：
- 定义注册请求/响应 DTO
- 定义登录请求/响应 DTO
- 定义 Token 刷新 DTO
- 定义用户信息响应 DTO

**文件**：
- `app/dto/__init__.py`
- `app/dto/auth/__init__.py`
- `app/dto/auth/register.py`
- `app/dto/auth/login.py`
- `app/dto/auth/token.py`
- `app/dto/user/__init__.py`
- `app/dto/user/user_response.py`
- `app/dto/common/__init__.py`
- `app/dto/common/response.py`

---

### Step 7: 业务逻辑层

**任务**：
- 实现 AuthService（注册、登录、Token 刷新）
- 实现 UserService（用户查询）

**文件**：
- `app/service/__init__.py`
- `app/service/auth_service.py`
- `app/service/user_service.py`

---

### Step 8: API 路由层

**任务**：
- 实现认证路由
- 实现依赖注入
- 路由聚合

**文件**：
- `app/api/__init__.py`
- `app/api/deps.py`
- `app/api/v1/__init__.py`
- `app/api/v1/auth.py`
- `app/api/v1/router.py`

---

### Step 9: 中间件

**任务**：
- 全局异常处理
- 请求日志中间件

**文件**：
- `app/middleware/__init__.py`
- `app/middleware/error_handler.py`

---

### Step 10: 应用入口

**任务**：
- 创建 FastAPI 应用
- 注册路由
- 注册中间件
- 初始化 Beanie（MongoDB）
- 初始化 Redis
- 配置 CORS

**文件**：
- `app/__init__.py`
- `app/main.py`

---

### Step 11: 测试

**任务**：
- pytest 配置
- 单元测试（Service 层）
- 集成测试（API 层）

**文件**：
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/api/test_auth.py`

---

### Step 12: WebSocket 连接管理器

**任务**：
- 实现 WebSocketConnectionManager 类
- 实现连接注册、注销
- 实现单连接限制（踢掉旧连接）
- 实现心跳检测
- 实现消息广播

**文件**：
- `app/service/ws_manager.py`

**核心类设计**：
```python
class WebSocketConnectionManager:
    """WebSocket 连接管理器"""

    # 映射关系
    _session_to_user: Dict[str, str]      # session_id → user_id
    _user_to_ws: Dict[str, WebSocket]      # user_id → websocket
    _ws_to_session: Dict[WebSocket, str]   # websocket → session_id

    # 心跳相关
    _last_ping_time: Dict[str, datetime]   # session_id → last_ping_time
    _heartbeat_task: Optional[asyncio.Task]

    async def connect(websocket: WebSocket, token: str) -> str:
        """建立连接，返回 session_id"""

    async def disconnect(websocket: WebSocket):
        """断开连接，清理映射"""

    async def kick_user(user_id: str, reason: str):
        """踢掉用户现有连接"""

    async def send_to_user(user_id: str, message: dict):
        """向指定用户发送消息"""

    async def start_heartbeat():
        """启动心跳检测任务"""

    async def handle_pong(session_id: str):
        """处理心跳响应"""
```

---

### Step 13: WebSocket 路由

**任务**：
- 实现 WebSocket 端点
- 实现 Token 认证
- 实现消息分发

**文件**：
- `app/api/v1/ws.py`

---

### Step 14: WebSocket DTO

**任务**：
- 定义消息类型枚举
- 定义请求消息 DTO
- 定义响应消息 DTO

**文件**：
- `app/dto/ws/__init__.py`
- `app/dto/ws/message.py`
- `app/dto/ws/response.py`

---

### Step 15: WebSocket 测试

**任务**：
- WebSocket 连接认证测试
- 单连接限制测试
- 心跳检测测试
- 消息处理测试

**文件**：
- `tests/api/test_ws.py`

---

## Rollback & Compatibility (回滚与兼容)

### 回滚方案

1. **代码回滚**：通过 Git 回退到上一个稳定版本
2. **数据回滚**：
   - MongoDB：删除测试数据
   - Redis：清空缓存

### 兼容性

| 项目 | 兼容性说明 |
|-----|-----------|
| Python | >= 3.11 |
| MongoDB | >= 6.0 |
| Redis | >= 7.0 |

### 数据迁移

- 本期为新系统，无需数据迁移
- 后续版本变更使用 Beanie Migration

---

## Configuration (配置)

### 环境变量

```bash
# 应用配置
APP_NAME=AIWorkHelper
APP_VERSION=0.1.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=aiworkhelper

# Redis
REDIS_URI=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_DAYS=7
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# WebSocket 配置
WS_HEARTBEAT_INTERVAL=30        # 心跳间隔（秒）
WS_HEARTBEAT_TIMEOUT=60         # 心跳超时（秒）
WS_MAX_MESSAGE_SIZE=1048576     # 最大消息大小（字节，默认 1MB）
```

---

## Dependencies (依赖关系)

```
main.py
  │
  ├─▶ config/settings.py       (配置)
  ├─▶ api/v1/router.py         (路由)
  │     │
  │     └─▶ api/v1/auth.py     (认证路由)
  │           │
  │           ├─▶ service/auth_service.py
  │           │     │
  │           │     └─▶ repository/user_repository.py
  │           │           │
  │           │           └─▶ entity/user.py
  │           │
  │           └─▶ dto/auth/*.py
  │
  ├─▶ security/dependencies.py (认证依赖)
  │     │
  │     ├─▶ security/jwt.py
  │     └─▶ security/password.py
  │
  └─▶ middleware/error_handler.py
```

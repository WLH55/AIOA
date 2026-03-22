# API: 用户认证模块接口定义

## Overview

本文档定义用户认证模块的所有 API 接口，包括注册、登录、Token 刷新、用户信息查询。

**Base URL**: `http://localhost:8000`

**WebSocket URL**: `ws://localhost:8000`

**认证方式**: Bearer Token (JWT)

---

## 1. 用户注册

### 基本信息

| 项目 | 值 |
|-----|---|
| Method | POST |
| Path | `/api/v1/auth/register` |
| Auth | 不需要 |
| Idempotency | 否（重复注册返回错误）|

### Request

#### Headers
```
Content-Type: application/json
```

#### Body

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|-----|------|------|------|---------|
| username | string | 是 | 用户名 | 3-50 字符，字母数字下划线 |
| email | string | 是 | 邮箱 | 有效邮箱格式 |
| password | string | 是 | 密码 | 最小 8 位，必须包含字母和数字 |
| full_name | string | 否 | 真实姓名 | 最大 100 字符 |
| department | string | 否 | 部门 | 最大 50 字符 |
| position | string | 否 | 职位 | 最大 50 字符 |
| employee_id | string | 否 | 工号 | 最大 50 字符 |
| phone | string | 否 | 手机号 | 符合手机号格式 |

#### Example

```json
{
  "username": "zhangsan",
  "email": "zhangsan@company.com",
  "password": "Password123",
  "full_name": "张三",
  "department": "技术部",
  "position": "后端工程师",
  "employee_id": "E001",
  "phone": "13800138000"
}
```

### Response (Success)

#### Status Code
```
201 Created
```

#### Body

统一响应格式（`ApiResponse`）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| code | int | 响应码，200 表示成功 |
| message | string | 响应消息 |
| data | object | 响应数据 |

**data 对象**：

| 字段 | 类型 | 说明 |
|-----|------|------|
| user_id | string | 用户唯一标识（MongoDB ObjectId）|
| username | string | 用户名 |
| email | string | 邮箱 |

#### Example

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "username": "zhangsan",
    "email": "zhangsan@company.com"
  }
}
```

### Error Codes

| 错误码 | HTTP Status | 含义 | 触发条件 |
|--------|-------------|------|---------|
| VALIDATION_ERROR | 422 | 请求参数校验失败 | 字段格式/类型不正确 |
| USERNAME_EXISTS | 400 | 用户名已存在 | username 已被注册 |
| EMAIL_EXISTS | 400 | 邮箱已存在 | email 已被注册 |

#### Error Response Example

```json
{
  "code": 400,
  "message": "Username already exists",
  "data": null
}
```

---

## 2. 用户登录

### 基本信息

| 项目 | 值 |
|-----|---|
| Method | POST |
| Path | `/api/v1/auth/login` |
| Auth | 不需要 |
| Idempotency | 是 |

### Request

#### Headers
```
Content-Type: application/json
```

#### Body

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|-----|------|------|------|---------|
| username | string | 是* | 用户名或邮箱 | 与 password 二选一 |
| email | string | 是* | 邮箱 | 与 username 二选一 |
| password | string | 是 | 密码 | - |

> 注：username 和 email 至少提供一个，优先使用 username

#### Example

```json
{
  "username": "zhangsan",
  "password": "Password123"
}
```

或使用邮箱登录：

```json
{
  "email": "zhangsan@company.com",
  "password": "Password123"
}
```

### Response (Success)

#### Status Code
```
200 OK
```

#### Body

统一响应格式（`ApiResponse`）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| code | int | 响应码，200 表示成功 |
| message | string | 响应消息 |
| data | object | 响应数据 |

**data 对象**：

| 字段 | 类型 | 说明 |
|-----|------|------|
| access_token | string | JWT Access Token |
| refresh_token | string | JWT Refresh Token |
| token_type | string | 固定值 "bearer" |
| expires_in | number | Access Token 过期时间（秒）|
| user | object | 用户信息 |

**user 对象**：

| 字段 | 类型 | 说明 |
|-----|------|------|
| user_id | string | 用户 ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| full_name | string\|null | 真实姓名 |
| roles | array | 角色列表 |

#### Example

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDdmMWY3N2JjZjg2Y2Q3OTk0MzkwMTEiLCJleHAiOjE2Nzg5NjY0MDAsInR5cGUiOiJhY2Nlc3MifQ.signature",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDdmMWY3N2JjZjg2Y2Q3OTk0MzkwMTEiLCJleHAiOjE2Nzk1NzEyMDAsInR5cGUiOiJyZWZyZXNoInQ.signature",
    "token_type": "bearer",
    "expires_in": 604800,
    "user": {
      "user_id": "507f1f77bcf86cd799439011",
      "username": "zhangsan",
      "email": "zhangsan@company.com",
      "full_name": "张三",
      "roles": ["user"]
    }
  }
}
```

### Error Codes

| 错误码 | HTTP Status | 含义 | 触发条件 |
|--------|-------------|------|---------|
| VALIDATION_ERROR | 422 | 请求参数校验失败 | 缺少必填字段 |
| INVALID_CREDENTIALS | 401 | 用户名或密码错误 | 用户不存在或密码不匹配 |
| USER_INACTIVE | 403 | 用户已被禁用 | 用户状态为 inactive/suspended |

#### Error Response Example

```json
{
  "code": 401,
  "message": "Invalid username or password",
  "data": null
}
```

---

## 3. Token 刷新

### 基本信息

| 项目 | 值 |
|-----|---|
| Method | POST |
| Path | `/api/v1/auth/refresh` |
| Auth | 不需要（使用 refresh_token）|
| Idempotency | 否 |

### Request

#### Headers
```
Content-Type: application/json
```

#### Body

| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|-----|------|------|------|---------|
| refresh_token | string | 是 | Refresh Token | 有效且未过期的 JWT |

#### Example

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Response (Success)

#### Status Code
```
200 OK
```

#### Body

统一响应格式（`ApiResponse`）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| code | int | 响应码，200 表示成功 |
| message | string | 响应消息 |
| data | object | 响应数据 |

**data 对象**：

| 字段 | 类型 | 说明 |
|-----|------|------|
| access_token | string | 新的 JWT Access Token |
| token_type | string | 固定值 "bearer" |
| expires_in | number | Access Token 过期时间（秒）|

#### Example

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 604800
  }
}
```

### Error Codes

| 错误码 | HTTP Status | 含义 | 触发条件 |
|--------|-------------|------|---------|
| INVALID_TOKEN | 401 | Token 无效 | Token 格式错误或签名验证失败 |
| EXPIRED_TOKEN | 401 | Token 已过期 | refresh_token 已过期 |
| INVALID_TOKEN_TYPE | 401 | Token 类型错误 | Token 不是 refresh_token |

#### Error Response Example

```json
{
  "code": 401,
  "message": "Refresh token has expired",
  "data": null
}
```

---

## 4. 获取当前用户信息

### 基本信息

| 项目 | 值 |
|-----|---|
| Method | GET |
| Path | `/api/v1/auth/me` |
| Auth | 需要（Bearer Token）|
| Idempotency | 是 |

### Request

#### Headers
```
Authorization: Bearer {access_token}
```

#### Example

```bash
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response (Success)

#### Status Code
```
200 OK
```

#### Body

统一响应格式（`ApiResponse`）：

| 字段 | 类型 | 说明 |
|-----|------|------|
| code | int | 响应码，200 表示成功 |
| message | string | 响应消息 |
| data | object | 响应数据 |

**data 对象**：

| 字段 | 类型 | 说明 |
|-----|------|------|
| user_id | string | 用户 ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| full_name | string\|null | 真实姓名 |
| department | string\|null | 部门 |
| position | string\|null | 职位 |
| employee_id | string\|null | 工号 |
| phone | string\|null | 手机号 |
| avatar_url | string\|null | 头像 URL |
| status | string | 状态：active/inactive/suspended |
| roles | array | 角色列表 |
| created_at | string | 创建时间（ISO 8601）|
| updated_at | string | 更新时间（ISO 8601）|
| last_login_at | string\|null | 最后登录时间（ISO 8601）|

#### Example

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "username": "zhangsan",
    "email": "zhangsan@company.com",
    "full_name": "张三",
    "department": "技术部",
    "position": "后端工程师",
    "employee_id": "E001",
    "phone": "13800138000",
    "avatar_url": null,
    "status": "active",
    "roles": ["user"],
    "created_at": "2026-03-15T10:30:00Z",
    "updated_at": "2026-03-15T10:30:00Z",
    "last_login_at": "2026-03-15T14:25:00Z"
  }
}
```

### Error Codes

| 错误码 | HTTP Status | 含义 | 触发条件 |
|--------|-------------|------|---------|
| UNAUTHORIZED | 401 | 未认证 | 缺少或无效的 Authorization Header |
| INVALID_TOKEN | 401 | Token 无效 | Token 签名验证失败 |
| EXPIRED_TOKEN | 401 | Token 已过期 | access_token 已过期 |
| USER_NOT_FOUND | 404 | 用户不存在 | Token 中的 user_id 找不到对应用户 |

#### Error Response Example

```json
{
  "code": 401,
  "message": "Not authenticated",
  "data": null
}
```

---

## 5. 用户登出

### 基本信息

| 项目 | 值 |
|-----|---|
| Method | POST |
| Path | `/api/v1/auth/logout` |
| Auth | 需要（Bearer Token）|
| Idempotency | 是 |

### Request

#### Headers
```
Authorization: Bearer {access_token}
```

#### Example

```bash
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response (Success)

#### Status Code
```
200 OK
```

#### Body

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "message": "Logged out successfully"
  }
}
```

> **注**: 本期不实现 Token 黑名单，客户端删除 Token 即可

---

## JWT Token 规范

### Access Token 结构

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "507f1f77bcf86cd799439011",
    "username": "zhangsan",
    "type": "access",
    "exp": 1678966400,
    "iat": 1678361600
  }
}
```

### Refresh Token 结构

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "507f1f77bcf86cd799439011",
    "type": "refresh",
    "exp": 1679571200,
    "iat": 1678361600
  }
}
```

### Token 有效期

| Token 类型 | 有效期 | 说明 |
|-----------|--------|------|
| Access Token | 7 天 (604800 秒) | 用于 API 认证 |
| Refresh Token | 30 天 (2592000 秒) | 用于刷新 Access Token |

---

## 数据模型

### User Entity

```python
class User(Document):
    user_id: str                    # 主键（与 _id 相同）
    username: str                   # 用户名（唯一）
    email: str                      # 邮箱（唯一）
    password_hash: str              # 密码哈值（bcrypt）
    full_name: str | None           # 真实姓名
    department: str | None          # 部门
    position: str | None            # 职位
    employee_id: str | None         # 工号
    phone: str | None               # 手机号
    avatar_url: str | None          # 头像 URL
    status: str                     # 状态: active/inactive/suspended
    roles: List[str]                # 角色列表
    created_at: datetime            # 创建时间
    updated_at: datetime            # 更新时间
    last_login_at: datetime | None  # 最后登录时间
```

---

## 通用错误格式

所有错误响应遵循统一格式（`ApiResponse`）：

```json
{
  "code": 400,
  "message": "错误描述",
  "data": null
}
```

### 常见错误码

| HTTP Status | 说明 |
|-------------|------|
| 400 | 请求参数错误（用户名/邮箱已存在等）|
| 401 | 未认证或 Token 无效/过期 |
| 403 | 权限不足（用户被禁用）|
| 404 | 资源不存在 |
| 422 | 请求参数校验失败 |
| 500 | 服务器内部错误 |

---

## 接口调用顺序示例

```
1. 注册用户
   POST /api/v1/auth/register

2. 用户登录
   POST /api/v1/auth/login
   → 获得 access_token 和 refresh_token

3. 访问受保护接口
   GET /api/v1/auth/me
   Header: Authorization: Bearer {access_token}

4. Token 过期后刷新
   POST /api/v1/auth/refresh
   → 获得新的 access_token

5. 登出
   POST /api/v1/auth/logout

6. 建立 WebSocket 连接
   ws://localhost:8000/api/v1/ws/chat
   Header: Authorization: Bearer {access_token}
   → 连接成功，开始 AI 聊天
```

---

## WebSocket 接口定义

### 6. WebSocket 连接

#### 基本信息

| 项目 | 值 |
|-----|---|
| URL | `ws://localhost:8000/api/v1/ws/chat` |
| 协议 | WebSocket (RFC 6455) |
| 认证 | Bearer Token (通过 Header 传递) |
| 消息格式 | JSON |

#### 连接认证

**请求头**：
```
Authorization: Bearer {access_token}
```

**连接成功响应**：
```json
{
  "type": "connected",
  "user_id": "507f1f77bcf86cd799439011",
  "username": "zhangsan",
  "session_id": "sess_abc123",
  "timestamp": "2026-03-22T10:30:00Z"
}
```

**认证失败响应**：

| 错误码 | 含义 | 触发条件 |
|--------|------|---------|
| 4001 | 未认证 | 缺少 Authorization Header |
| 4002 | Token 无效 | Token 格式错误或签名验证失败 |
| 4003 | Token 已过期 | access_token 已过期 |
| 4004 | 用户不存在 | Token 中的 user_id 找不到对应用户 |

**错误响应示例**：
```json
{
  "type": "error",
  "code": 4001,
  "message": "Authentication required"
}
```

---

#### 消息类型定义

##### 客户端 → 服务端

###### 1. 聊天消息

```json
{
  "type": "chat",
  "content": "你好，请帮我写一份周报",
  "conversation_id": "conv_001",
  "options": {
    "stream": true
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| type | string | 是 | 固定值 "chat" |
| content | string | 是 | 用户消息内容 |
| conversation_id | string | 否 | 会话 ID，不传则新建会话 |
| options | object | 否 | 可选参数 |
| options.stream | boolean | 否 | 是否流式返回，默认 true |

###### 2. 心跳响应

```json
{
  "type": "pong"
}
```

###### 3. 关闭连接

```json
{
  "type": "close"
}
```

---

##### 服务端 → 客户端

###### 1. 连接成功

```json
{
  "type": "connected",
  "user_id": "507f1f77bcf86cd799439011",
  "username": "zhangsan",
  "session_id": "sess_abc123",
  "timestamp": "2026-03-22T10:30:00Z"
}
```

###### 2. 聊天消息响应（流式）

```json
{
  "type": "message",
  "content": "好的，我来帮您写周报...",
  "conversation_id": "conv_001",
  "message_id": "msg_001",
  "is_final": false,
  "timestamp": "2026-03-22T10:30:01Z"
}
```

| 字段 | 类型 | 说明 |
|-----|------|------|
| type | string | 固定值 "message" |
| content | string | AI 响应内容片段 |
| conversation_id | string | 会话 ID |
| message_id | string | 消息 ID |
| is_final | boolean | 是否为最后一条消息 |
| timestamp | string | 时间戳（ISO 8601）|

###### 3. 心跳检测

```json
{
  "type": "ping"
}
```

客户端需在 60 秒内响应 `{"type": "pong"}`，否则连接将被断开。

###### 4. 被踢下线

```json
{
  "type": "kicked",
  "reason": "new_login",
  "message": "您的账号在其他设备登录，当前连接已断开"
}
```

| reason | 说明 |
|--------|------|
| new_login | 新设备登录，踢掉旧连接 |
| server_shutdown | 服务器关闭 |

###### 5. 错误消息

```json
{
  "type": "error",
  "code": 5001,
  "message": "AI service unavailable",
  "conversation_id": "conv_001"
}
```

**错误码范围**：

| 范围 | 类别 |
|-----|------|
| 4001-4099 | 认证错误 |
| 5001-5099 | 服务端错误 |
| 6001-6099 | 业务错误 |

---

#### 心跳机制

| 项目 | 值 |
|-----|---|
| 心跳间隔 | 30 秒 |
| 响应超时 | 60 秒 |
| 超时处理 | 断开连接 |

**流程**：
1. 服务端每 30 秒发送 `{"type": "ping"}`
2. 客户端需在 60 秒内响应 `{"type": "pong"}`
3. 超时未响应，服务端主动断开连接

---

#### 单连接限制

同一用户同时只能有一个 WebSocket 连接：

1. 用户 A 在设备 1 建立连接
2. 用户 A 在设备 2 建立新连接
3. 设备 1 收到 `{"type": "kicked", "reason": "new_login"}`
4. 设备 1 连接被关闭
5. 设备 2 连接成功

---

#### 连接关闭

**正常关闭**：
- 客户端发送 `{"type": "close"}`
- 服务端响应后关闭连接

**异常关闭**：
- 心跳超时
- Token 过期
- 服务端错误
- 网络中断

关闭时服务端清理：
- 删除 `sessionId → userId` 映射
- 删除 `userId → websocket` 映射
- 记录断开日志

# API: 用户认证模块接口定义

## Overview

本文档定义用户认证模块的所有 API 接口，包括注册、登录、Token 刷新、用户信息查询。

**Base URL**: `http://localhost:8000`

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

| 字段 | 类型 | 说明 |
|-----|------|------|
| user_id | string | 用户唯一标识（MongoDB ObjectId）|
| username | string | 用户名 |
| email | string | 邮箱 |

#### Example

```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "username": "zhangsan",
  "email": "zhangsan@company.com"
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
  "detail": "Username already exists",
  "code": "USERNAME_EXISTS"
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

| 字段 | 类型 | 说明 |
|-----|------|------|
| access_token | string | JWT Access Token |
| refresh_token | string | JWT Refresh Token |
| token_type | string | 固定值 "bearer" |
| expires_in | number | Access Token 过期时间（秒）|
| user | object | 用户信息 |

#### user 对象

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
  "detail": "Invalid username or password",
  "code": "INVALID_CREDENTIALS"
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

| 字段 | 类型 | 说明 |
|-----|------|------|
| access_token | string | 新的 JWT Access Token |
| token_type | string | 固定值 "bearer" |
| expires_in | number | Access Token 过期时间（秒）|

#### Example

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
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
  "detail": "Refresh token has expired",
  "code": "EXPIRED_TOKEN"
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
  "detail": "Not authenticated",
  "code": "UNAUTHORIZED"
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
  "message": "Logged out successfully"
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

所有错误响应遵循以下格式：

```json
{
  "detail": "错误描述",
  "code": "ERROR_CODE",
  "timestamp": "2026-03-15T14:25:00Z"
}
```

### 常见错误码

| 错误码 | HTTP Status | 说明 |
|--------|-------------|------|
| VALIDATION_ERROR | 422 | 请求参数校验失败 |
| UNAUTHORIZED | 401 | 未认证 |
| INVALID_CREDENTIALS | 401 | 用户名或密码错误 |
| INVALID_TOKEN | 401 | Token 无效 |
| EXPIRED_TOKEN | 401 | Token 已过期 |
| USERNAME_EXISTS | 400 | 用户名已存在 |
| EMAIL_EXISTS | 400 | 邮箱已存在 |
| USER_NOT_FOUND | 404 | 用户不存在 |
| USER_INACTIVE | 403 | 用户已被禁用 |

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
```

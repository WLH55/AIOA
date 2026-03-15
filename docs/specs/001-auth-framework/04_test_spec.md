# Test Spec: 项目框架与用户认证模块

## Test Scope (测试范围)

| 层级 | 测试内容 | 覆盖范围 |
|-----|---------|---------|
| **单元测试** | Service 层业务逻辑、Repository 层数据访问、安全模块 | 核心函数、边界条件 |
| **集成测试** | API 层端到端测试 | 完整请求/响应流程 |
| **契约测试** | DTO 校验、Pydantic 模型 | 字段类型、校验规则 |
| **性能测试** | 登录接口、Token 验证 | 响应时间要求 |

---

## Test Strategy (测试策略)

### 单元测试策略

- 使用 `pytest` + `pytest-asyncio` 进行异步测试
- 使用 `pytest-mock` 进行依赖 Mock
- 覆盖率目标：>= 80%

### 集成测试策略

- 使用 `httpx.TestClient` 测试 FastAPI 接口
- 使用 `mongomock` 或测试用 MongoDB 实例
- 测试前清理数据，测试后隔离

### 测试数据准备

```python
# fixtures/test_user.py
test_users = [
    {
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "Password123",
        "full_name": "测试用户1",
        "employee_id": "E001"
    },
    {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "Password456",
        "full_name": "测试用户2",
        "employee_id": "E002"
    }
]
```

---

## Test Cases (用例列表)

### TC1: 用户注册 - 正常流程

| 编号 | TC001 |
|-----|-------|
| **场景** | 使用有效数据注册新用户 |
| **前置条件** | 用户名和邮箱未被注册 |
| **测试步骤** | 1. POST /api/v1/auth/register<br>2. 携带完整有效参数 |
| **期望结果** | 201 Created，返回 user_id、username、email |
| **数据库验证** | users 集合中新增一条记录，password_hash 格式正确 |

**请求示例**：
```json
POST /api/v1/auth/register
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "Password123",
  "full_name": "新用户",
  "employee_id": "E003"
}
```

**期望响应**：
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "username": "newuser",
  "email": "new@example.com"
}
```

---

### TC2: 用户注册 - 用户名重复

| 编号 | TC002 |
|-----|-------|
| **场景** | 使用已存在的用户名注册 |
| **前置条件** | 用户名 "testuser1" 已存在 |
| **测试步骤** | 1. POST /api/v1/auth/register<br>2. 使用已存在的 username |
| **期望结果** | 400 Bad Request，错误码 USERNAME_EXISTS |

**期望响应**：
```json
{
  "detail": "Username already exists",
  "code": "USERNAME_EXISTS"
}
```

---

### TC3: 用户注册 - 邮箱重复

| 编号 | TC003 |
|-----|-------|
| **场景** | 使用已存在的邮箱注册 |
| **前置条件** | 邮箱 "test1@example.com" 已存在 |
| **测试步骤** | 1. POST /api/v1/auth/register<br>2. 使用已存在的 email |
| **期望结果** | 400 Bad Request，错误码 EMAIL_EXISTS |

---

### TC4: 用户注册 - 密码强度不足

| 编号 | TC004 |
|-----|-------|
| **场景** | 使用弱密码注册 |
| **前置条件** | 无 |
| **测试步骤** | 1. POST /api/v1/auth/register<br>2. password = "123456" |
| **期望结果** | 422 Unprocessable Entity，字段校验失败 |

**请求示例**：
```json
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "123456"
}
```

**期望响应**：
```json
{
  "detail": "Password must be at least 8 characters with letters and numbers"
}
```

---

### TC5: 用户注册 - 缺少必填字段

| 编号 | TC005 |
|-----|-------|
| **场景** | 缺少必填字段 |
| **前置条件** | 无 |
| **测试步骤** | 1. POST /api/v1/auth/register<br>2. 不携带 email 字段 |
| **期望结果** | 422 Unprocessable Entity |

---

### TC6: 用户登录 - 用户名登录成功

| 编号 | TC006 |
|-----|-------|
| **场景** | 使用用户名和密码登录 |
| **前置条件** | 用户 "testuser1" 已存在，密码 "Password123" |
| **测试步骤** | 1. POST /api/v1/auth/login<br>2. 携带正确的 username 和 password |
| **期望结果** | 200 OK，返回 access_token、refresh_token、user 信息 |
| **数据库验证** | last_login_at 字段更新 |

**请求示例**：
```json
{
  "username": "testuser1",
  "password": "Password123"
}
```

**期望响应**：
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "user_id": "...",
    "username": "testuser1",
    "email": "test1@example.com"
  }
}
```

---

### TC7: 用户登录 - 邮箱登录成功

| 编号 | TC007 |
|-----|-------|
| **场景** | 使用邮箱和密码登录 |
| **前置条件** | 邮箱 "test1@example.com" 已存在 |
| **测试步骤** | 1. POST /api/v1/auth/login<br>2. 使用 email 和 password |
| **期望结果** | 200 OK，返回 Token |

---

### TC8: 用户登录 - 密码错误

| 编号 | TC008 |
|-----|-------|
| **场景** | 使用错误的密码登录 |
| **前置条件** | 用户 "testuser1" 已存在 |
| **测试步骤** | 1. POST /api/v1/auth/login<br>2. password = "WrongPassword" |
| **期望结果** | 401 Unauthorized，错误码 INVALID_CREDENTIALS |

**期望响应**：
```json
{
  "detail": "Invalid username or password",
  "code": "INVALID_CREDENTIALS"
}
```

---

### TC9: 用户登录 - 用户不存在

| 编号 | TC009 |
|-----|-------|
| **场景** | 使用不存在的用户名登录 |
| **前置条件** | 用户 "nonexist" 不存在 |
| **测试步骤** | 1. POST /api/v1/auth/login<br>2. username = "nonexist" |
| **期望结果** | 401 Unauthorized，错误码 INVALID_CREDENTIALS |

---

### TC10: 用户登录 - 用户被禁用

| 编号 | TC010 |
|-----|-------|
| **场景** | 登录被禁用的用户 |
| **前置条件** | 用户状态为 "suspended" |
| **测试步骤** | 1. POST /api/v1/auth/login<br>2. 使用被禁用用户的凭证 |
| **期望结果** | 403 Forbidden，错误码 USER_INACTIVE |

---

### TC11: 获取用户信息 - 有 Token

| 编号 | TC011 |
|-----|-------|
| **场景** | 使用有效 Token 获取用户信息 |
| **前置条件** | 已登录，获得 access_token |
| **测试步骤** | 1. GET /api/v1/auth/me<br>2. Header: Authorization: Bearer {token} |
| **期望结果** | 200 OK，返回完整用户信息 |

**期望响应**：
```json
{
  "user_id": "...",
  "username": "testuser1",
  "email": "test1@example.com",
  "full_name": "测试用户1",
  "status": "active",
  "roles": ["user"],
  "created_at": "2026-03-15T10:30:00Z",
  "last_login_at": "2026-03-15T14:25:00Z"
}
```

---

### TC12: 获取用户信息 - 无 Token

| 编号 | TC012 |
|-----|-------|
| **场景** | 不携带 Token 访问受保护接口 |
| **前置条件** | 无 |
| **测试步骤** | 1. GET /api/v1/auth/me<br>2. 不携带 Authorization Header |
| **期望结果** | 401 Unauthorized |

---

### TC13: 获取用户信息 - Token 过期

| 编号 | TC013 |
|-----|-------|
| **场景** | 使用已过期的 Token |
| **前置条件** | Token 已过期（exp < 当前时间）|
| **测试步骤** | 1. GET /api/v1/auth/me<br>2. 携带过期 Token |
| **期望结果** | 401 Unauthorized，错误码 EXPIRED_TOKEN |

---

### TC14: 获取用户信息 - Token 格式错误

| 编号 | TC014 |
|-----|-------|
| **场景** | Token 格式不正确 |
| **前置条件** | 无 |
| **测试步骤** | 1. GET /api/v1/auth/me<br>2. Authorization: "InvalidToken" |
| **期望结果** | 401 Unauthorized |

---

### TC15: Token 刷新 - 成功

| 编号 | TC015 |
|-----|-------|
| **场景** | 使用有效 refresh_token 获取新 access_token |
| **前置条件** | 已登录，获得 refresh_token |
| **测试步骤** | 1. POST /api/v1/auth/refresh<br>2. 携带 refresh_token |
| **期望结果** | 200 OK，返回新的 access_token |

**请求示例**：
```json
{
  "refresh_token": "eyJhbGci..."
}
```

**期望响应**：
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

---

### TC16: Token 刷新 - Refresh Token 过期

| 编号 | TC016 |
|-----|-------|
| **场景** | 使用已过期的 refresh_token |
| **前置条件** | refresh_token 已过期 |
| **测试步骤** | 1. POST /api/v1/auth/refresh<br>2. 携带过期 refresh_token |
| **期望结果** | 401 Unauthorized，错误码 EXPIRED_TOKEN |

---

### TC17: Token 刷新 - 使用 Access Token

| 编号 | TC017 |
|-----|-------|
| **场景** | 使用 access_token 代替 refresh_token |
| **前置条件** | 无 |
| **测试步骤** | 1. POST /api/v1/auth/refresh<br>2. 使用 access_token |
| **期望结果** | 401 Unauthorized，错误码 INVALID_TOKEN_TYPE |

---

### TC18: 密码哈希 - 正确性验证

| 编号 | TC018 |
|-----|-------|
| **场景** | 验证密码哈希算法正确性 |
| **前置条件** | 用户已注册 |
| **测试步骤** | 1. 查询数据库 password_hash<br>2. 验证格式为 $2b$12$...<br>3. 使用 verify_password 验证 |
| **期望结果** | 密码哈希格式正确，验证成功 |

---

### TC19: JWT 编解码 - 正确性验证

| 编号 | TC019 |
|-----|-------|
| **场景** | 验证 JWT 编解码正确性 |
| **前置条件** | 无 |
| **测试步骤** | 1. create_access_token(user)<br>2. decode_jwt(token)<br>3. 验证 payload 内容 |
| **期望结果** | payload 包含正确的 sub、type、exp |

---

### TC20: 并发注册 - 用户名唯一性

| 编号 | TC020 |
|-----|-------|
| **场景** | 并发注册相同用户名 |
| **前置条件** | 无 |
| **测试步骤** | 1. 同时发送 10 个相同用户名的注册请求<br>2. 验证只有一个成功 |
| **期望结果** | 只有第一个请求成功，其余返回 USERNAME_EXISTS |

---

## Data Preparation (数据准备)

### 前置数据

```python
# tests/conftest.py
@pytest.fixture
async def test_users(db):
    """创建测试用户"""
    users = []
    for i in range(1, 6):
        user = User(
            username=f"testuser{i}",
            email=f"test{i}@example.com",
            password_hash=hash_password("Password123"),
            full_name=f"测试用户{i}",
            employee_id=f"E00{i}",
            status="active"
        )
        await user.save()
        users.append(user)
    return users

@pytest.fixture
def auth_headers(test_users):
    """返回认证头"""
    token = create_access_token(test_users[0])
    return {"Authorization": f"Bearer {token}"}
```

### Mock 依赖

```python
# tests/conftest.py
@pytest.fixture
def mock_redis():
    """Mock Redis 客户端"""
    with patch("app.config.settings.get_redis") as mock:
        yield mock

@pytest.fixture
def mock_mongo():
    """Mock MongoDB 连接"""
    with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock:
        yield mock
```

---

## Performance Tests (性能测试)

### PT1: 登录接口响应时间

| 指标 | 要求 |
|-----|------|
| **响应时间** | < 500ms (P95) |
| **并发** | 100 请求/秒 |
| **测试方法** | 使用 locust 或 pytest-benchmark |

```python
# tests/performance/test_login_performance.py
def test_login_response_time(client, test_user):
    """测试登录响应时间"""
    response = client.post("/api/v1/auth/login", json={
        "username": test_user.username,
        "password": "Password123"
    })
    assert response.status_code == 200
    assert response.elapsed.total_seconds() < 0.5
```

### PT2: Token 验证响应时间

| 指标 | 要求 |
|-----|------|
| **响应时间** | < 50ms (P95) |
| **测试方法** | 直接调用 get_current_user |

---

## Regression Impact (回归影响)

### 可能影响的老功能

本期为新模块，无老功能影响。

### 未来可能受影响的功能

| 模块 | 影响说明 |
|-----|---------|
| 待办管理 | 依赖用户认证 |
| 审批管理 | 依赖用户认证和角色 |
| AI Agent | 依赖用户上下文 |

---

## Test Execution (测试执行)

### 运行所有测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/api/test_auth.py

# 运行特定测试用例
pytest tests/api/test_auth.py::test_register_success

# 详细输出
pytest -v

# 显示打印输出
pytest -s
```

### CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
```

---

## Test Checklist (测试检查清单)

### 单元测试

- [ ] password_hash() 生成正确格式的哈希
- [ ] verify_password() 验证密码正确性
- [ ] create_access_token() 生成正确 JWT
- [ ] create_refresh_token() 生成正确 JWT
- [ ] decode_jwt() 正确解码并验证
- [ ] user_repository.create() 创建用户
- [ ] user_repository.find_by_username() 查询用户
- [ ] user_repository.find_by_email() 查询用户
- [ ] auth_service.register() 注册逻辑
- [ ] auth_service.login() 登录逻辑
- [ ] auth_service.refresh_token() 刷新逻辑

### 集成测试

- [ ] POST /api/v1/auth/register - 正常注册
- [ ] POST /api/v1/auth/register - 用户名重复
- [ ] POST /api/v1/auth/register - 邮箱重复
- [ ] POST /api/v1/auth/register - 密码强度不足
- [ ] POST /api/v1/auth/login - 用户名登录成功
- [ ] POST /api/v1/auth/login - 邮箱登录成功
- [ ] POST /api/v1/auth/login - 密码错误
- [ ] POST /api/v1/auth/login - 用户不存在
- [ ] POST /api/v1/auth/login - 用户被禁用
- [ ] GET /api/v1/auth/me - 有 Token
- [ ] GET /api/v1/auth/me - 无 Token
- [ ] GET /api/v1/auth/me - Token 过期
- [ ] POST /api/v1/auth/refresh - 成功
- [ ] POST /api/v1/auth/refresh - Token 过期
- [ ] POST /api/v1/auth/refresh - Token 类型错误

### 性能测试

- [ ] 登录接口响应时间 < 500ms
- [ ] Token 验证延迟 < 50ms

### 覆盖率目标

- [ ] 总体覆盖率 >= 80%
- [ ] Service 层覆盖率 >= 90%
- [ ] API 层覆盖率 >= 70%

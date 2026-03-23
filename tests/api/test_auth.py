"""
认证接口集成测试

测试用户注册、登录、Token 刷新等 API 端点
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.security.jwt import decode_jwt, create_access_token, create_refresh_token
from app.security.password import hash_password
from tests.conftest import TEST_USER_DATA, TEST_LOGIN_DATA, WEAK_PASSWORD_DATA


class TestRegister:
    """用户注册测试类"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """TC001: 正常注册新用户"""
        response = await client.post("/api/v1/auth/register", json=TEST_USER_DATA)

        # 201 Created 是正确的创建响应状态码
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == TEST_USER_DATA["name"]
        assert "user_id" in data["data"]

    @pytest.mark.asyncio
    async def test_register_username_exists(self, client: AsyncClient, test_user: User):
        """TC002: 用户名重复注册"""
        response = await client.post("/api/v1/auth/register", json={
            "name": test_user.name,
            "password": "Password123",
        })

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """TC003: 密码强度不足"""
        response = await client.post("/api/v1/auth/register", json=WEAK_PASSWORD_DATA)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_required_field(self, client: AsyncClient):
        """TC004: 缺少必填字段"""
        response = await client.post("/api/v1/auth/register", json={
            "name": "newuser",
            # 缺少 password
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_username_format(self, client: AsyncClient):
        """TC005: 无效用户名格式（包含特殊字符）"""
        response = await client.post("/api/v1/auth/register", json={
            "name": "user@name!",
            "password": "Password123",
        })

        assert response.status_code == 422


class TestLogin:
    """用户登录测试类"""

    @pytest.mark.asyncio
    async def test_login_with_username_success(self, client: AsyncClient, test_user: User):
        """TC006: 用户名登录成功"""
        response = await client.post("/api/v1/auth/login", json={
            "name": "testuser1",
            "password": "Password123",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["name"] == "testuser1"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """TC007: 密码错误"""
        response = await client.post("/api/v1/auth/login", json={
            "name": "testuser1",
            "password": "WrongPassword",
        })

        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_login_user_not_exists(self, client: AsyncClient):
        """TC008: 用户不存在"""
        response = await client.post("/api/v1/auth/login", json={
            "name": "nonexistuser",
            "password": "Password123",
        })

        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_login_user_suspended(self, client: AsyncClient, suspended_user: User):
        """TC009: 用户被禁用"""
        response = await client.post("/api/v1/auth/login", json={
            "name": "suspended_user",
            "password": "Password123",
        })

        assert response.status_code == 400
        data = response.json()
        assert "inactive" in data["message"].lower() or "suspended" in data["message"].lower()


class TestGetCurrentUser:
    """获取当前用户测试类"""

    @pytest.mark.asyncio
    async def test_get_current_user_with_token(self, client: AsyncClient, auth_headers: dict):
        """TC010: 使用有效 Token 获取用户信息"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "testuser1"

    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, client: AsyncClient):
        """TC011: 不携带 Token"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """TC012: Token 格式错误"""
        response = await client.get("/api/v1/auth/me", headers={
            "Authorization": "InvalidToken"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_bearer(self, client: AsyncClient):
        """TC013: Bearer 格式错误"""
        response = await client.get("/api/v1/auth/me", headers={
            "Authorization": "BearerInvalidToken"
        })

        assert response.status_code == 401


class TestTokenRefresh:
    """Token 刷新测试类"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, refresh_token: str):
        """TC014: Token 刷新成功"""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_with_access_token(self, client: AsyncClient, auth_headers: dict, test_user: User):
        """TC015: 使用 Access Token 刷新（应该失败）"""
        access_token = create_access_token(str(test_user.id), test_user.name)

        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token
        })

        assert response.status_code == 400
        data = response.json()
        assert "token type" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """TC016: 无效 Token"""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })

        assert response.status_code == 400


class TestLogout:
    """用户登出测试类"""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, auth_headers: dict):
        """TC017: 登出成功"""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        """TC018: 无 Token"""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401


class TestPasswordVerification:
    """密码验证相关测试"""

    @pytest.mark.asyncio
    async def test_password_stored_as_hash(self, client: AsyncClient):
        """TC019: 验证密码以哈希形式存储"""
        await client.post("/api/v1/auth/register", json=TEST_USER_DATA)

        # 从数据库获取用户
        user = await User.find_one(User.name == TEST_USER_DATA["name"])

        assert user is not None
        # 密码应该是哈希值，不是明文
        assert user.password != TEST_USER_DATA["password"]
        # bcrypt 格式
        assert user.password.startswith("$2b$")


class TestJwtContent:
    """JWT 内容验证测试"""

    @pytest.mark.asyncio
    async def test_jwt_contains_correct_user_id(self, client: AsyncClient, test_user: User):
        """TC020: JWT 包含正确的用户 ID"""
        response = await client.post("/api/v1/auth/login", json={
            "name": "testuser1",
            "password": "Password123",
        })

        data = response.json()
        access_token = data["data"]["access_token"]

        payload = decode_jwt(access_token)

        assert payload is not None
        assert payload["sub"] == str(test_user.id)
        assert payload["type"] == "access"
"""
JWT 模块单元测试

测试 JWT Token 的生成和解码功能
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    get_token_payload,
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
)
from app.config.settings import settings


class TestCreateAccessToken:
    """Access Token 生成测试类"""

    def test_create_access_token_returns_string(self):
        """测试生成 Token 返回字符串"""
        token = create_access_token("user123", "testuser")

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_user_id(self):
        """测试 Token 包含用户 ID"""
        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(user_id, "testuser")

        payload = decode_jwt(token)

        assert payload is not None
        assert payload["sub"] == user_id

    def test_create_access_token_contains_username(self):
        """测试 Token 包含用户名"""
        username = "testuser"
        token = create_access_token("user123", username)

        payload = decode_jwt(token)

        assert payload is not None
        assert payload["username"] == username

    def test_create_access_token_type(self):
        """测试 Token 类型为 access"""
        token = create_access_token("user123", "testuser")

        payload = decode_jwt(token)

        assert payload is not None
        assert payload["type"] == ACCESS_TOKEN_TYPE

    def test_create_access_token_has_expiration(self):
        """测试 Token 包含过期时间"""
        token = create_access_token("user123", "testuser")

        payload = decode_jwt(token)

        assert payload is not None
        assert "exp" in payload
        assert payload["exp"] > datetime.utcnow().timestamp()

    def test_create_access_token_has_issued_at(self):
        """测试 Token 包含签发时间"""
        token = create_access_token("user123", "testuser")

        payload = decode_jwt(token)

        assert payload is not None
        assert "iat" in payload

    def test_create_access_token_custom_expiration(self):
        """测试自定义过期时间"""
        custom_delta = timedelta(hours=1)
        token = create_access_token("user123", "testuser", expires_delta=custom_delta)

        payload = decode_jwt(token)

        assert payload is not None
        # 验证过期时间在预期范围内（允许 60 秒误差）
        # 使用 UTC 时间进行比较
        now = datetime.utcnow()
        expected_exp = now + custom_delta
        # fromtimestamp 默认返回本地时间，需要转换为 UTC
        actual_exp = datetime.utcfromtimestamp(payload["exp"])

        # 允许 60 秒误差
        assert abs((actual_exp - expected_exp).total_seconds()) < 60


class TestCreateRefreshToken:
    """Refresh Token 生成测试类"""

    def test_create_refresh_token_returns_string(self):
        """测试生成 Token 返回字符串"""
        token = create_refresh_token("user123")

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_user_id(self):
        """测试 Token 包含用户 ID"""
        user_id = "507f1f77bcf86cd799439011"
        token = create_refresh_token(user_id)

        payload = decode_jwt(token)

        assert payload is not None
        assert payload["sub"] == user_id

    def test_create_refresh_token_type(self):
        """测试 Token 类型为 refresh"""
        token = create_refresh_token("user123")

        payload = decode_jwt(token)

        assert payload is not None
        assert payload["type"] == REFRESH_TOKEN_TYPE

    def test_create_refresh_token_no_username(self):
        """测试 Refresh Token 不包含用户名"""
        token = create_refresh_token("user123")

        payload = decode_jwt(token)

        assert payload is not None
        assert "username" not in payload

    def test_create_refresh_token_custom_expiration(self):
        """测试自定义过期时间"""
        custom_delta = timedelta(days=60)
        token = create_refresh_token("user123", expires_delta=custom_delta)

        payload = decode_jwt(token)

        assert payload is not None
        now = datetime.utcnow()
        expected_exp = now + custom_delta
        # 使用 UTC 时间
        actual_exp = datetime.utcfromtimestamp(payload["exp"])

        # 允许 60 秒误差
        assert abs((actual_exp - expected_exp).total_seconds()) < 60


class TestDecodeJwt:
    """JWT 解码测试类"""

    def test_decode_jwt_valid_token(self):
        """测试解码有效 Token"""
        user_id = "user123"
        token = create_access_token(user_id, "testuser")

        payload = decode_jwt(token)

        assert payload is not None
        assert payload["sub"] == user_id

    def test_decode_jwt_invalid_token(self):
        """测试解码无效 Token"""
        invalid_token = "invalid.token.here"

        payload = decode_jwt(invalid_token)

        assert payload is None

    def test_decode_jwt_wrong_signature(self):
        """测试解码错误签名的 Token"""
        import jwt

        # 使用错误密钥生成 Token
        payload = {"sub": "user123", "type": "access"}
        wrong_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        result = decode_jwt(wrong_token)

        assert result is None

    def test_decode_jwt_expired_token(self):
        """测试解码过期 Token"""
        # 创建已过期的 Token
        expired_delta = timedelta(seconds=-1)
        token = create_access_token("user123", "testuser", expires_delta=expired_delta)

        payload = decode_jwt(token)

        assert payload is None


class TestGetTokenPayload:
    """获取 Token Payload 测试类"""

    def test_get_token_payload_valid_token(self):
        """测试获取有效 Token 的 payload"""
        token = create_access_token("user123", "testuser")

        payload = get_token_payload(token)

        assert payload is not None
        assert payload["sub"] == "user123"

    def test_get_token_payload_expired_token(self):
        """测试获取过期 Token 的 payload（不验证过期）"""
        expired_delta = timedelta(seconds=-1)
        token = create_access_token("user123", "testuser", expires_delta=expired_delta)

        payload = get_token_payload(token)

        # 即使过期，也应该返回 payload
        assert payload is not None
        assert payload["sub"] == "user123"

    def test_get_token_payload_invalid_token(self):
        """测试获取无效 Token 的 payload"""
        invalid_token = "invalid.token.here"

        payload = get_token_payload(invalid_token)

        assert payload is None


class TestTokenTypeDifference:
    """Token 类型差异测试类"""

    def test_access_and_refresh_different(self):
        """测试 Access Token 和 Refresh Token 不同"""
        user_id = "user123"
        access_token = create_access_token(user_id, "testuser")
        refresh_token = create_refresh_token(user_id)

        assert access_token != refresh_token

    def test_token_types_can_be_distinguished(self):
        """测试可以区分 Token 类型"""
        user_id = "user123"
        access_token = create_access_token(user_id, "testuser")
        refresh_token = create_refresh_token(user_id)

        access_payload = decode_jwt(access_token)
        refresh_payload = decode_jwt(refresh_token)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
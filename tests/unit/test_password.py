"""
密码模块单元测试

测试密码哈希和验证功能
"""
import pytest
from app.security.password import hash_password, verify_password


class TestPasswordHash:
    """密码哈希测试类"""

    def test_hash_password_returns_string(self):
        """测试哈希返回字符串"""
        password = "Password123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_format(self):
        """测试哈希格式正确（bcrypt 格式）"""
        password = "Password123"
        hashed = hash_password(password)

        # bcrypt 格式: $2b$12$...
        assert hashed.startswith("$2b$12$")

    def test_hash_password_different_each_time(self):
        """测试相同密码每次生成不同的哈希（盐值不同）"""
        password = "Password123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_hash_password_different_passwords(self):
        """测试不同密码生成不同的哈希"""
        hash1 = hash_password("Password123")
        hash2 = hash_password("Password456")

        assert hash1 != hash2


class TestVerifyPassword:
    """密码验证测试类"""

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "Password123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """测试错误密码验证"""
        password = "Password123"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_case_sensitive(self):
        """测试密码区分大小写"""
        password = "Password123"
        hashed = hash_password(password)

        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False

    def test_verify_password_empty(self):
        """测试空密码"""
        password = "Password123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False

    def test_verify_password_special_characters(self):
        """测试特殊字符密码"""
        password = "P@ssw0rd!#$%"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("P@ssw0rd!#$", hashed) is False

    def test_verify_password_long_password(self):
        """测试长密码"""
        password = "A" * 100 + "1"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_unicode(self):
        """测试 Unicode 密码"""
        password = "密码测试123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("密码测试456", hashed) is False
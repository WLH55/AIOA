"""
认证服务层

处理用户注册、登录、Token 管理等业务逻辑
"""
import logging
from typing import Optional

from app.config.settings import settings
from app.config.exceptions import BusinessValidationException, ResourceNotFoundException
from app.models.user import User
from app.repository.user_repository import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token, decode_jwt
from app.dto.auth.register import RegisterRequest, RegisterResponse
from app.dto.auth.login import LoginRequest, LoginResponse
from app.dto.auth.token import TokenRefreshRequest, TokenRefreshResponse
from app.dto.user.user_response import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """
    认证服务类

    提供用户注册、登录、Token 管理等业务逻辑
    """

    @staticmethod
    async def register(request: RegisterRequest) -> RegisterResponse:
        """
        用户注册

        流程：
        1. 检查用户名是否已存在
        2. 创建用户记录
        3. 返回用户信息

        Args:
            request: 注册请求 DTO

        Returns:
            注册响应 DTO

        Raises:
            BusinessValidationException: 用户名已存在
        """
        # 检查用户名是否已存在
        if await UserRepository.exists_by_name(request.name):
            raise BusinessValidationException("Username already exists")

        # 创建用户
        user = User(
            name=request.name,
            password=hash_password(request.password),
            status=0,
            isAdmin=False,
        )

        # 保存用户
        user = await UserRepository.create(user)

        logger.info(f"用户注册成功: {user.name}")

        return RegisterResponse(
            user_id=str(user.id),
            name=user.name,
        )

    @staticmethod
    async def login(request: LoginRequest) -> LoginResponse:
        """
        用户登录

        流程：
        1. 根据用户名查找用户
        2. 验证用户存在且状态正常
        3. 验证密码
        4. 更新时间戳
        5. 生成 Token
        6. 返回登录响应

        Args:
            request: 登录请求 DTO

        Returns:
            登录响应 DTO

        Raises:
            BusinessValidationException: 用户名/密码错误或用户被禁用
        """
        # 查找用户
        user = await UserRepository.find_by_name(request.name)

        # 验证用户存在（使用统一错误消息防止用户名枚举）
        if not user:
            logger.warning(f"登录失败: 用户不存在 ({request.name})")
            raise BusinessValidationException("Invalid username or password")

        # 验证用户状态（1-启用，0-禁用）
        if user.status == 0:
            logger.warning(f"登录失败: 用户被禁用 ({user.name})")
            raise BusinessValidationException("用户已被禁用，请联系管理员")

        # 验证密码
        if not verify_password(request.password, user.password):
            logger.warning(f"登录失败: 密码错误 ({user.name})")
            raise BusinessValidationException("Invalid username or password")

        # 更新时间戳
        user.update_timestamp()
        await UserRepository.update(user)

        # 生成 Token
        access_token = create_access_token(str(user.id), user.name)
        refresh_token = create_refresh_token(str(user.id))

        logger.info(f"用户登录成功: {user.name}")

        # 计算过期时间戳
        access_expire = int((user.updateAt / 1000) + settings.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60) * 1000
        refresh_after = access_expire - 5 * 60 * 1000  # 提前5分钟刷新

        return LoginResponse(
            status=user.status,
            id=str(user.id),
            name=user.name,
            token=access_token,
            accessExpire=access_expire,
            refreshAfter=refresh_after,
        )

    @staticmethod
    async def refresh_token(request: TokenRefreshRequest) -> TokenRefreshResponse:
        """
        刷新 Token

        流程：
        1. 解码 refresh_token
        2. 验证 Token 类型和有效期
        3. 查询用户
        4. 验证用户状态
        5. 生成新的 access_token
        6. 返回响应

        Args:
            request: Token 刷新请求 DTO

        Returns:
            Token 刷新响应 DTO

        Raises:
            BusinessValidationException: Token 无效或用户状态异常
        """
        # 解码 Token
        payload = decode_jwt(request.refresh_token)
        if not payload:
            raise BusinessValidationException("Invalid token")

        # 验证 Token 类型
        token_type = payload.get("type")
        if token_type != "refresh":
            raise BusinessValidationException("Invalid token type")

        # 获取用户 ID
        user_id = payload.get("sub")
        if not user_id:
            raise BusinessValidationException("Invalid token payload")

        # 查询用户
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise BusinessValidationException("User not found")

        # 验证用户状态（1=启用，0=禁用）
        if user.status == 0:
            raise BusinessValidationException("用户已被禁用")

        # 生成新的 Access Token
        access_token = create_access_token(str(user.id), user.name)

        logger.info(f"Token 刷新成功: {user.name}")

        return TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    @staticmethod
    async def get_user_info(user_id: str) -> UserResponse:
        """
        获取用户信息

        Args:
            user_id: 用户 ID

        Returns:
            用户响应 DTO

        Raises:
            ResourceNotFoundException: 用户不存在
        """
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found")

        return UserResponse.from_user(user)
"""
认证路由模块

提供用户注册、登录、Token 刷新、用户信息查询等 API 端点
"""
import logging

from fastapi import APIRouter, Depends, status

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.auth_service import AuthService
from app.dto.auth.register import RegisterRequest, RegisterResponse
from app.dto.auth.login import LoginRequest, LoginResponse
from app.dto.auth.token import TokenRefreshRequest, TokenRefreshResponse
from app.dto.user.user_response import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=ApiResponse[RegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="使用用户名和密码注册新用户",
)
async def register(request: RegisterRequest) -> ApiResponse[RegisterResponse]:
    """
    用户注册接口

    - **name**: 用户名（3-50字符，字母数字下划线）
    - **password**: 密码（最小8位，必须包含字母和数字）
    """
    response = await AuthService.register(request)
    return ApiResponse.success(data=response, message="注册成功")


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    summary="用户登录",
    description="使用用户名和密码登录，返回 JWT Token",
)
async def login(request: LoginRequest) -> ApiResponse[LoginResponse]:
    """
    用户登录接口

    - **name**: 用户名
    - **password**: 密码
    """
    response = await AuthService.login(request)
    return ApiResponse.success(data=response, message="登录成功")


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenRefreshResponse],
    summary="刷新 Token",
    description="使用 refresh_token 获取新的 access_token",
)
async def refresh_token(request: TokenRefreshRequest) -> ApiResponse[TokenRefreshResponse]:
    """
    Token 刷新接口

    - **refresh_token**: JWT Refresh Token
    """
    response = await AuthService.refresh_token(request)
    return ApiResponse.success(data=response, message="Token 刷新成功")


@router.post(
    "/logout",
    response_model=ApiResponse[dict],
    summary="用户登出",
    description="用户登出（客户端删除 Token 即可，服务端暂不实现 Token 黑名单）",
)
async def logout(current_user: User = Depends(get_current_user)) -> ApiResponse[dict]:
    """
    用户登出接口

    需要携带有效的 Bearer Token
    """
    logger.info(f"用户登出: {current_user.name}")
    return ApiResponse.success(data={"message": "Logged out successfully"})


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="获取当前用户信息",
    description="获取当前认证用户的详细信息",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserResponse]:
    """
    获取当前用户信息接口

    需要携带有效的 Bearer Token
    """
    response = await AuthService.get_user_info(str(current_user.id))
    return ApiResponse.success(data=response)
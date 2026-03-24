"""
用户路由模块

提供用户管理相关的 API 端点
"""
import logging

from fastapi import APIRouter, Depends, status

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.user_service import UserService
from app.dto.user.user_request import UserRequest, UserListRequest, UpdatePasswordRequest
from app.dto.user.user_response import UserResponse, UserListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post(
    "/login",
    response_model=ApiResponse[dict],
    summary="用户登录",
    description="使用用户名和密码登录，返回 JWT Token",
)
async def login(request: dict) -> ApiResponse[dict]:
    """
    用户登录接口

    注意: 此接口复用 AuthService 的登录逻辑
    实际登录逻辑在 /auth/login 中实现
    """
    # 登录逻辑已在 auth_service.py 中实现
    # 此接口保留以兼容 Java 版本的 API 路径
    from app.services.auth_service import AuthService
    from app.dto.auth.login import LoginRequest

    login_request = LoginRequest(name=request.get("name"), password=request.get("password"))
    response = await AuthService.login(login_request)
    return ApiResponse.success(data=response.model_dump(), message="登录成功")


@router.get(
    "/list",
    response_model=ApiResponse[UserListResponse],
    summary="用户列表",
    description="查询用户列表，支持分页和筛选",
)
async def list_users(
    request: UserListRequest = Depends(),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserListResponse]:
    """
    用户列表接口

    需要携带有效的 Bearer Token
    """
    response = await UserService.list(request)
    return ApiResponse.success(data=response)


@router.post(
    "/password",
    response_model=ApiResponse[dict],
    summary="修改密码",
    description="修改用户密码（管理员可修改任意用户密码，普通用户只能修改自己密码）",
)
async def update_password(
    request: UpdatePasswordRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    修改密码接口

    需要携带有效的 Bearer Token
    """
    await UserService.update_password(request, current_user)
    return ApiResponse.success(message="修改密码成功")


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="获取用户信息",
    description="根据用户ID获取用户详细信息",
)
async def get_user_info(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserResponse]:
    """
    获取用户信息接口

    需要携带有效的 Bearer Token
    """
    response = await UserService.info(user_id)
    return ApiResponse.success(data=response)


@router.post(
    "",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户",
)
async def create_user(
    request: UserRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    创建用户接口

    需要携带有效的 Bearer Token
    """
    await UserService.create(request, current_user)
    return ApiResponse.success(message="创建用户成功")


@router.put(
    "",
    response_model=ApiResponse[dict],
    summary="编辑用户",
    description="编辑用户信息（管理员可编辑任意用户，普通用户只能编辑自己）",
)
async def edit_user(
    request: UserRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    编辑用户接口

    需要携带有效的 Bearer Token
    """
    await UserService.edit(request, current_user)
    return ApiResponse.success(message="编辑用户成功")


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[dict],
    summary="删除用户",
    description="删除指定用户（仅管理员可操作）",
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    删除用户接口

    需要携带有效的 Bearer Token
    """
    await UserService.delete(user_id, current_user)
    return ApiResponse.success(message="删除用户成功")

"""
部门路由模块

提供部门管理相关的 API 端点
"""
import logging

from fastapi import APIRouter, Depends, status

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.department_service import DepartmentService
from app.dto.department.department_request import (
    DepartmentRequest,
    SetDepartmentUsersRequest,
    AddDepartmentUserRequest,
    RemoveDepartmentUserRequest,
)
from app.dto.department.department_response import DepartmentResponse, DepartmentTreeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dep", tags=["部门管理"])


@router.get(
    "/soa",
    response_model=ApiResponse[DepartmentTreeResponse],
    summary="获取部门树结构",
    description="获取完整的部门树形结构",
)
async def get_department_tree(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[DepartmentTreeResponse]:
    """
    获取部门树结构接口

    需要携带有效的 Bearer Token
    返回完整的部门层级树
    """
    response = await DepartmentService.soa()
    return ApiResponse.success(data=response)


@router.get(
    "/{department_id}",
    response_model=ApiResponse[DepartmentResponse],
    summary="获取部门详情",
    description="根据部门ID获取部门详细信息",
)
async def get_department_info(
    department_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[DepartmentResponse]:
    """
    获取部门详情接口

    需要携带有效的 Bearer Token
    """
    response = await DepartmentService.info(department_id)
    return ApiResponse.success(data=response)


@router.post(
    "",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="创建部门",
    description="创建新部门",
)
async def create_department(
    request: DepartmentRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    创建部门接口

    需要携带有效的 Bearer Token
    """
    await DepartmentService.create(request)
    return ApiResponse.success(message="创建部门成功")


@router.put(
    "",
    response_model=ApiResponse[dict],
    summary="更新部门",
    description="更新部门信息",
)
async def edit_department(
    request: DepartmentRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    更新部门接口

    需要携带有效的 Bearer Token
    """
    await DepartmentService.edit(request)
    return ApiResponse.success(message="更新部门成功")


@router.delete(
    "/{department_id}",
    response_model=ApiResponse[dict],
    summary="删除部门",
    description="删除指定部门",
)
async def delete_department(
    department_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    删除部门接口

    需要携带有效的 Bearer Token
    注意: 部门下有用户时不能删除
    """
    await DepartmentService.delete(department_id)
    return ApiResponse.success(message="删除部门成功")


@router.post(
    "/user",
    response_model=ApiResponse[dict],
    summary="设置部门用户",
    description="批量设置部门的用户列表",
)
async def set_department_users(
    request: SetDepartmentUsersRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    设置部门用户接口

    需要携带有效的 Bearer Token
    """
    await DepartmentService.set_department_users(request)
    return ApiResponse.success(message="设置部门用户成功")


@router.post(
    "/user/add",
    response_model=ApiResponse[dict],
    summary="添加部门员工",
    description="添加员工到部门（级联到上级部门）",
)
async def add_department_user(
    request: AddDepartmentUserRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    添加部门员工接口

    需要携带有效的 Bearer Token
    员工会自动添加到所有上级部门
    """
    await DepartmentService.add_department_user(request)
    return ApiResponse.success(message="添加部门员工成功")


@router.delete(
    "/user/remove",
    response_model=ApiResponse[dict],
    summary="删除部门员工",
    description="从部门删除员工（级联从上级部门删除）",
)
async def remove_department_user(
    request: RemoveDepartmentUserRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    删除部门员工接口

    需要携带有效的 Bearer Token
    注意: 不能删除部门负责人
    """
    await DepartmentService.remove_department_user(request)
    return ApiResponse.success(message="删除部门员工成功")


@router.get(
    "/user/{user_id}",
    response_model=ApiResponse[DepartmentResponse],
    summary="获取用户部门信息",
    description="获取用户的部门信息（包含完整的上级部门层级）",
)
async def get_user_department_info(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[DepartmentResponse]:
    """
    获取用户部门信息接口

    需要携带有效的 Bearer Token
    返回用户所属部门及其上级部门的完整层级结构
    """
    response = await DepartmentService.department_user_info(user_id)
    return ApiResponse.success(data=response)
"""
群组路由模块

提供群组管理相关的 API 端点
"""
import logging

from fastapi import APIRouter, Depends, status

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.group_service import GroupService
from app.dto.group.group_request import (
    CreateGroupRequest,
    GroupListRequest,
    InviteMemberRequest,
    RemoveMemberRequest,
    UpdateGroupRequest,
)
from app.dto.group.group_response import (
    GroupResponse,
    GroupListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/group", tags=["群组管理"])


@router.post(
    "/create",
    response_model=ApiResponse[str],
    status_code=status.HTTP_201_CREATED,
    summary="创建群组",
    description="创建新的群组",
)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[str]:
    """
    创建群组接口

    需要携带有效的 Bearer Token
    """
    group_id = await GroupService.create(request, current_user)
    return ApiResponse.success(data=group_id, message="创建群组成功")


@router.get(
    "/list",
    response_model=ApiResponse[GroupListResponse],
    summary="获取群组列表",
    description="查询当前用户参与的群组列表，支持分页",
)
async def list_groups(
    request: GroupListRequest = Depends(),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[GroupListResponse]:
    """
    获取群组列表接口

    需要携带有效的 Bearer Token
    返回当前用户参与的所有群组
    """
    response = await GroupService.list(request, current_user)
    return ApiResponse.success(data=response)


@router.get(
    "/{group_id}",
    response_model=ApiResponse[GroupResponse],
    summary="获取群组详情",
    description="根据群组ID获取详细信息",
)
async def get_group_info(
    group_id: str,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[GroupResponse]:
    """
    获取群组详情接口

    需要携带有效的 Bearer Token
    """
    response = await GroupService.info(group_id, current_user)
    return ApiResponse.success(data=response)


@router.post(
    "/{group_id}/invite",
    response_model=ApiResponse[None],
    summary="邀请成员",
    description="邀请新成员加入群组（仅群主）",
)
async def invite_members(
    group_id: str,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    """
    邀请成员接口

    需要携带有效的 Bearer Token
    只有群主可以邀请成员
    """
    await GroupService.invite(group_id, request, current_user)
    return ApiResponse.success(message="邀请成员成功")


@router.post(
    "/{group_id}/remove",
    response_model=ApiResponse[None],
    summary="移除成员",
    description="从群组中移除成员（仅群主）",
)
async def remove_member(
    group_id: str,
    request: RemoveMemberRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    """
    移除成员接口

    需要携带有效的 Bearer Token
    只有群主可以移除成员
    """
    await GroupService.remove(group_id, request, current_user)
    return ApiResponse.success(message="移除成员成功")


@router.post(
    "/{group_id}/exit",
    response_model=ApiResponse[None],
    summary="退出群组",
    description="成员主动退出群组",
)
async def exit_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    """
    退出群组接口

    需要携带有效的 Bearer Token
    群主不能退出群组
    """
    await GroupService.exit(group_id, current_user)
    return ApiResponse.success(message="退出群组成功")


@router.put(
    "/{group_id}",
    response_model=ApiResponse[None],
    summary="修改群组信息",
    description="修改群组名称、头像等信息（仅群主）",
)
async def update_group(
    group_id: str,
    request: UpdateGroupRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    """
    修改群组信息接口

    需要携带有效的 Bearer Token
    只有群主可以修改群组信息
    """
    await GroupService.update(group_id, request, current_user)
    return ApiResponse.success(message="修改群组信息成功")


@router.delete(
    "/{group_id}",
    response_model=ApiResponse[None],
    summary="解散群组",
    description="解散群组（仅群主）",
)
async def dismiss_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[None]:
    """
    解散群组接口

    需要携带有效的 Bearer Token
    只有群主可以解散群组
    """
    await GroupService.dismiss(group_id, current_user)
    return ApiResponse.success(message="解散群组成功")

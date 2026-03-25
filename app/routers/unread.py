"""
未读消息计数路由模块

提供未读消息计数相关的 API 端点
"""
import logging

from fastapi import APIRouter, Depends

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.unread_service import UnreadService
from app.dto.unread.unread_request import GetUnreadListRequest, ClearUnreadRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat/unread", tags=["未读消息"])


@router.post("/list", response_model=ApiResponse, summary="获取未读消息列表")
async def get_unread_list(
    request: GetUnreadListRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    获取当前用户的未读消息计数列表

    需要携带有效的 Bearer Token
    """
    logger.info(f"获取未读列表: userId={current_user.id}, conversationType={request.conversationType}")

    data = await UnreadService.get_list(
        userId=str(current_user.id),
        conversationType=request.conversationType,
    )

    return ApiResponse.success(data=data, message="获取成功")


@router.post("/clear", response_model=ApiResponse, summary="清除会话未读计数")
async def clear_unread(
    request: ClearUnreadRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    清除指定会话的未读计数

    需要携带有效的 Bearer Token
    """
    logger.info(f"清除未读: userId={current_user.id}, conversationId={request.conversationId}")

    await UnreadService.clear(
        userId=str(current_user.id),
        conversationId=request.conversationId,
    )

    return ApiResponse.success(message="清除成功")
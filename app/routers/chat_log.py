"""
聊天记录路由模块

提供聊天记录管理相关的 API 端点
"""
import logging

from fastapi import APIRouter, Depends, status

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.chat_log_service import ChatLogService
from app.dto.chat_log.chat_log_request import ChatLogRequest, ChatLogListRequest
from app.dto.chat_log.chat_log_response import ChatLogResponse, ChatLogListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天记录"])


@router.get(
    "/list",
    response_model=ApiResponse[ChatLogListResponse],
    summary="聊天记录列表",
    description="查询聊天记录列表，支持分页和筛选",
)
async def list_chat_logs(
    request: ChatLogListRequest = Depends(),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ChatLogListResponse]:
    """
    聊天记录列表接口

    需要携带有效的 Bearer Token
    支持按会话ID、发送者ID、聊天类型、时间范围筛选
    """
    response = await ChatLogService.list(request)
    return ApiResponse.success(data=response)


@router.get(
    "/conversation/{conversation_id}",
    response_model=ApiResponse[ChatLogListResponse],
    summary="按会话查询聊天记录",
    description="根据会话ID查询聊天记录列表",
)
async def list_chat_logs_by_conversation(
    conversation_id: str,
    page: int = 1,
    count: int = 20,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ChatLogListResponse]:
    """
    按会话查询聊天记录接口

    需要携带有效的 Bearer Token
    返回指定会话的聊天记录列表
    """
    response = await ChatLogService.list_by_conversation(conversation_id, page, count)
    return ApiResponse.success(data=response)


@router.get(
    "/{chat_log_id}",
    response_model=ApiResponse[ChatLogResponse],
    summary="获取聊天记录详情",
    description="根据聊天记录ID获取详细信息",
)
async def get_chat_log_info(
    chat_log_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ChatLogResponse]:
    """
    获取聊天记录详情接口

    需要携带有效的 Bearer Token
    """
    response = await ChatLogService.info(chat_log_id)
    return ApiResponse.success(data=response)


@router.post(
    "",
    response_model=ApiResponse[str],
    status_code=status.HTTP_201_CREATED,
    summary="创建聊天记录",
    description="创建新的聊天记录",
)
async def create_chat_log(
    request: ChatLogRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[str]:
    """
    创建聊天记录接口

    需要携带有效的 Bearer Token
    """
    chat_log_id = await ChatLogService.create(request)
    return ApiResponse.success(data=chat_log_id, message="创建聊天记录成功")

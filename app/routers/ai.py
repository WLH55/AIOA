"""
AI 会话路由模块

提供 AI 会话管理的 HTTP API 端点
"""
import logging

from fastapi import APIRouter, Depends, status, Query

from app.config.schemas import ApiResponse
from app.dto.ai import CreateConversationRequest, DeleteConversationRequest
from app.dto.ai.ai_response import ConversationListResponse, MessageListResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.ai_conversation_service import AiConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI 对话"])


@router.post(
    "/conversation",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建 AI 会话",
    description="创建新的 AI 对话会话",
)
async def create_conversation(
    request: CreateConversationRequest = None,
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    创建 AI 会话接口

    需要携带有效的 Bearer Token
    """
    title = request.title if request else None
    response = await AiConversationService.create(current_user, title)
    return ApiResponse.success(data=response.model_dump(), message="创建 AI 会话成功")


@router.get(
    "/conversation/list",
    response_model=ApiResponse,
    summary="获取 AI 会话列表",
    description="获取当前用户的 AI 对话会话列表",
)
async def list_conversations(
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    获取 AI 会话列表接口

    需要携带有效的 Bearer Token
    """
    response = await AiConversationService.list_conversations(current_user, page, pageSize)
    return ApiResponse.success(data=response.model_dump())


@router.post(
    "/conversation/delete",
    response_model=ApiResponse,
    summary="删除 AI 会话",
    description="删除指定的 AI 对话会话（软删除）",
)
async def delete_conversation(
    request: DeleteConversationRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    删除 AI 会话接口

    需要携带有效的 Bearer Token
    """
    await AiConversationService.delete(current_user, request.conversationId)
    return ApiResponse.success(message="删除会话成功")


@router.get(
    "/conversation/{conversation_id}/messages",
    response_model=ApiResponse,
    summary="获取会话历史消息",
    description="获取指定 AI 会话的历史消息列表",
)
async def get_conversation_messages(
    conversation_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    获取会话历史消息接口

    需要携带有效的 Bearer Token
    消息按发送时间升序排列
    """
    response = await AiConversationService.get_messages(
        current_user, conversation_id, page, pageSize,
    )
    return ApiResponse.success(data=response.model_dump())

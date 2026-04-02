"""
AI 会话路由模块

提供 AI 会话管理的 HTTP API 端点和 SSE 流式对话端点
"""
import logging

from fastapi import APIRouter, Depends, Request, status, Query
from fastapi.responses import StreamingResponse

from app.config.schemas import ApiResponse
from app.dto.ai import CreateConversationRequest, DeleteConversationRequest, ChatStreamRequest
from app.dto.ai.ai_response import ConversationListResponse, MessageListResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.ai_chat_service import AiChatService
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


@router.post(
    "/chat/stream",
    summary="AI 对话 SSE 流式接口",
    description="通过 Server-Sent Events 流式返回 AI 对话响应",
)
async def chat_stream(
    request: ChatStreamRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    AI 对话 SSE 流式接口

    客户端发送 POST 请求，服务端以 SSE 格式流式返回 AI 响应。
    SSE 事件类型：ai_chunk、ai_tool_call、ai_tool_result、ai_complete、ai_error
    需要携带有效的 Bearer Token
    """
    redis_client = getattr(fastapi_request.app.state, "redis", None)
    if redis_client is None:
        return StreamingResponse(
            _error_sse_generator(request.conversationId, "AI 服务暂时不可用，请稍后重试"),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )
    generator = AiChatService.handle_ai_chat_sse(
        user=current_user,
        conversation_id=request.conversationId,
        content=request.content.strip(),
        redis_client=redis_client,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


def _sse_headers() -> dict:
    """
    返回 SSE 响应所需的 HTTP 头

    Returns:
        dict: SSE 响应头
    """
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


async def _error_sse_generator(conversation_id: str, message: str):
    """
    生成 SSE 错误事件

    Args:
        conversation_id: 会话 ID
        message: 错误消息

    Yields:
        str: SSE 格式错误事件
    """
    import json
    yield f"event: ai_error\ndata: {json.dumps({'conversationId': conversation_id, 'error': 'AI_SERVICE_ERROR', 'message': message}, ensure_ascii=False)}\n\n"

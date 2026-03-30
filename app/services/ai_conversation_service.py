"""
AI 会话管理服务

处理 AI 对话会话的创建、查询、删除和历史消息获取
"""
import logging
import time

from app.config import settings
from app.config.exceptions import BusinessValidationException, ResourceNotFoundException
from app.dto.ai.ai_response import (
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
)
from app.models.ai_conversation import AiConversation
from app.models.chat_log import ChatLog
from app.repository.ai_conversation_repository import AiConversationRepository
from app.repository.chat_log_repository import ChatLogRepository
from app.models.user import User

logger = logging.getLogger(__name__)

# AI 对话 chatType
CHAT_TYPE_AI = 3


class AiConversationService:
    """
    AI 会话管理服务

    提供会话 CRUD 和历史消息查询
    """

    @staticmethod
    async def create(current_user: User, title: str = None) -> ConversationResponse:
        """
        创建 AI 会话

        Args:
            current_user: 当前用户
            title: 会话标题（可选）

        Returns:
            会话响应 DTO

        Raises:
            BusinessValidationException: 会话数量超限
        """
        user_id = str(current_user.id)
        # 检查会话数量上限
        count = await AiConversationRepository.count_by_user_id(user_id)
        if count >= settings.AI_CONVERSATION_MAX_COUNT:
            raise BusinessValidationException(
                f"会话数量已达上限（{settings.AI_CONVERSATION_MAX_COUNT}），请删除旧会话后重试"
            )
        conversation = AiConversation(
            userId=user_id,
            title=title,
            status=1,
        )
        saved = await AiConversationRepository.create(conversation)
        return ConversationResponse(
            id=str(saved.id),
            userId=saved.userId,
            title=saved.title,
            status=saved.status,
            createdAt=saved.createdAt,
            updatedAt=saved.updatedAt,
        )

    @staticmethod
    async def list_conversations(
        current_user: User, page: int = 1, page_size: int = 20,
    ) -> ConversationListResponse:
        """
        获取用户的 AI 会话列表

        Args:
            current_user: 当前用户
            page: 页码
            page_size: 每页数量

        Returns:
            会话列表响应 DTO
        """
        user_id = str(current_user.id)
        conversations, total = await AiConversationRepository.find_by_user_id(
            user_id, page, page_size,
        )
        items = [
            ConversationResponse(
                id=str(conv.id),
                userId=conv.userId,
                title=conv.title,
                status=conv.status,
                createdAt=conv.createdAt,
                updatedAt=conv.updatedAt,
            )
            for conv in conversations
        ]
        return ConversationListResponse(list=items, total=total)

    @staticmethod
    async def delete(current_user: User, conversation_id: str) -> None:
        """
        删除 AI 会话（软删除）

        Args:
            current_user: 当前用户
            conversation_id: 会话 ID

        Raises:
            ResourceNotFoundException: 会话不存在
            BusinessValidationException: 无权操作
        """
        conversation = await AiConversationRepository.find_by_id(conversation_id)
        if not conversation:
            raise ResourceNotFoundException("会话不存在")
        if conversation.userId != str(current_user.id):
            raise BusinessValidationException("无权操作他人的会话")
        await AiConversationRepository.soft_delete(conversation_id)
        logger.info(f"AI 会话已删除: conversationId={conversation_id}, userId={current_user.id}")

    @staticmethod
    async def get_messages(
        current_user: User, conversation_id: str, page: int = 1, page_size: int = 20,
    ) -> MessageListResponse:
        """
        获取会话的历史消息

        Args:
            current_user: 当前用户
            conversation_id: 会话 ID
            page: 页码
            page_size: 每页数量

        Returns:
            消息列表响应 DTO

        Raises:
            ResourceNotFoundException: 会话不存在
            BusinessValidationException: 无权访问
        """
        conversation = await AiConversationRepository.find_by_id(conversation_id)
        if not conversation:
            raise ResourceNotFoundException("会话不存在")
        if conversation.userId != str(current_user.id):
            raise BusinessValidationException("无权访问他人的会话")
        chat_logs, total = await ChatLogRepository.find_by_conditions(
            conversation_id=conversation_id,
            chat_type=CHAT_TYPE_AI,
            page=page,
            page_size=page_size,
        )
        # 按 sendTime 升序排列
        chat_logs.sort(key=lambda x: x.sendTime)
        items = [
            MessageResponse(
                id=str(log.id),
                sendId=log.sendId,
                msgContent=log.msgContent,
                sendTime=log.sendTime,
            )
            for log in chat_logs
        ]
        return MessageListResponse(list=items, total=total)

    @staticmethod
    async def validate_conversation(conversation_id: str, user_id: str) -> AiConversation:
        """
        验证会话有效性和权限

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID

        Returns:
            会话对象

        Raises:
            ResourceNotFoundException: 会话不存在
            BusinessValidationException: 无权访问
        """
        conversation = await AiConversationRepository.find_active_by_id(conversation_id)
        if not conversation:
            raise ResourceNotFoundException("会话不存在或已删除")
        if conversation.userId != user_id:
            raise BusinessValidationException("无权访问他人的会话")
        return conversation

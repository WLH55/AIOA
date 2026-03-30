"""
AI 会话数据访问层

提供 AI 会话相关的数据库操作方法
"""
import logging
from typing import Optional, List

from app.models.ai_conversation import AiConversation

logger = logging.getLogger(__name__)


class AiConversationRepository:
    """
    AI 会话数据访问层

    封装所有 AI 会话相关的数据库操作
    """

    @staticmethod
    async def create(conversation: AiConversation) -> AiConversation:
        """
        创建 AI 会话

        Args:
            conversation: AiConversation 实体对象

        Returns:
            创建后的 AiConversation 对象
        """
        await conversation.insert()
        logger.info(f"AI 会话创建成功: userId={conversation.userId}")
        return conversation

    @staticmethod
    async def find_by_id(conversation_id: str) -> Optional[AiConversation]:
        """
        根据 ID 查询 AI 会话

        Args:
            conversation_id: 会话 ID

        Returns:
            AiConversation 对象或 None
        """
        from beanie import PydanticObjectId
        return await AiConversation.get(PydanticObjectId(conversation_id))

    @staticmethod
    async def find_active_by_id(conversation_id: str) -> Optional[AiConversation]:
        """
        根据 ID 查询活跃的 AI 会话

        Args:
            conversation_id: 会话 ID

        Returns:
            活跃状态的 AiConversation 对象或 None
        """
        from beanie import PydanticObjectId
        return await AiConversation.find_one(
            AiConversation.id == PydanticObjectId(conversation_id),
            AiConversation.status == 1,
        )

    @staticmethod
    async def find_by_user_id(
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[AiConversation], int]:
        """
        按用户 ID 分页查询活跃会话列表

        Args:
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量

        Returns:
            (会话列表, 总数)
        """
        skip = (page - 1) * page_size
        query = AiConversation.find(
            AiConversation.userId == user_id,
            AiConversation.status == 1,
        )
        total = await query.count()
        conversations = await query.skip(skip).limit(page_size).sort("-updatedAt").to_list()
        return conversations, total

    @staticmethod
    async def count_by_user_id(user_id: str) -> int:
        """
        统计用户的活跃会话数量

        Args:
            user_id: 用户 ID

        Returns:
            活跃会话数量
        """
        return await AiConversation.find(
            AiConversation.userId == user_id,
            AiConversation.status == 1,
        ).count()

    @staticmethod
    async def soft_delete(conversation_id: str) -> bool:
        """
        软删除 AI 会话

        Args:
            conversation_id: 会话 ID

        Returns:
            是否操作成功
        """
        conversation = await AiConversationRepository.find_by_id(conversation_id)
        if not conversation:
            return False
        conversation.status = 2
        conversation.update_timestamp()
        await conversation.save()
        logger.info(f"AI 会话软删除成功: id={conversation_id}")
        return True

    @staticmethod
    async def update_title(conversation_id: str, title: str) -> bool:
        """
        更新会话标题

        Args:
            conversation_id: 会话 ID
            title: 新标题

        Returns:
            是否更新成功
        """
        conversation = await AiConversationRepository.find_by_id(conversation_id)
        if not conversation:
            return False
        conversation.title = title[:50]
        conversation.update_timestamp()
        await conversation.save()
        logger.info(f"AI 会话标题更新: id={conversation_id}, title={title[:50]}")
        return True

    @staticmethod
    async def update_timestamp(conversation_id: str) -> None:
        """
        更新会话的最后更新时间

        Args:
            conversation_id: 会话 ID
        """
        conversation = await AiConversationRepository.find_by_id(conversation_id)
        if conversation:
            conversation.update_timestamp()
            await conversation.save()

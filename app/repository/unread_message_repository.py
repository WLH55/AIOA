"""
未读消息计数 Repository

提供未读消息计数的数据访问操作
"""
import logging
from typing import List, Optional

from beanie import PydanticObjectId

from app.models.unread_message import UnreadMessage

logger = logging.getLogger(__name__)


class UnreadMessageRepository:
    """
    未读消息计数数据访问类
    """

    @staticmethod
    async def create(
        userId: str,
        conversationId: str,
        conversationType: int,
        unreadCount: int = 0,
        lastReadTime: Optional[int] = None,
    ) -> UnreadMessage:
        """
        创建未读消息记录

        Args:
            userId: 用户ID
            conversationId: 会话ID
            conversationType: 会话类型
            unreadCount: 未读数量
            lastReadTime: 最后阅读时间

        Returns:
            创建的未读消息记录
        """
        unread = UnreadMessage(
            userId=userId,
            conversationId=conversationId,
            conversationType=conversationType,
            unreadCount=unreadCount,
            lastReadTime=lastReadTime,
        )
        await unread.insert()
        logger.debug(f"创建未读记录: userId={userId}, conversationId={conversationId}, count={unreadCount}")
        return unread

    @staticmethod
    async def find_by_user_id(
        userId: str,
        conversationType: Optional[int] = None,
    ) -> List[UnreadMessage]:
        """
        查询用户的所有未读记录

        Args:
            userId: 用户ID
            conversationType: 可选，过滤会话类型

        Returns:
            未读记录列表
        """
        query = {"userId": userId}
        if conversationType is not None:
            query["conversationType"] = conversationType

        unread_list = await UnreadMessage.find(query).to_list()
        return unread_list

    @staticmethod
    async def find_by_conversation(
        userId: str,
        conversationId: str,
    ) -> Optional[UnreadMessage]:
        """
        查询用户指定会话的未读记录

        Args:
            userId: 用户ID
            conversationId: 会话ID

        Returns:
            未读记录或 None
        """
        unread = await UnreadMessage.find_one({
            "userId": userId,
            "conversationId": conversationId,
        })
        return unread

    @staticmethod
    async def increment(
        userId: str,
        conversationId: str,
        conversationType: int,
        delta: int = 1,
    ) -> int:
        """
        增加未读计数

        Args:
            userId: 用户ID
            conversationId: 会话ID
            conversationType: 会话类型
            delta: 增加的数量

        Returns:
            更新后的未读数量
        """
        # 先尝试查找现有记录
        existing = await UnreadMessageRepository.find_by_conversation(userId, conversationId)

        if existing:
            # 更新现有记录
            existing.unreadCount = max(0, existing.unreadCount + delta)
            existing.update_timestamp()
            await existing.replace()
            logger.debug(f"增加未读: userId={userId}, conversationId={conversationId}, delta={delta}, newCount={existing.unreadCount}")
            return existing.unreadCount
        else:
            # 创建新记录
            new_count = max(0, delta)
            await UnreadMessageRepository.create(
                userId=userId,
                conversationId=conversationId,
                conversationType=conversationType,
                unreadCount=new_count,
            )
            logger.debug(f"创建未读记录: userId={userId}, conversationId={conversationId}, count={new_count}")
            return new_count

    @staticmethod
    async def clear(
        userId: str,
        conversationId: str,
    ) -> bool:
        """
        清除未读计数（设为 0）

        Args:
            userId: 用户ID
            conversationId: 会话ID

        Returns:
            是否清除成功
        """
        existing = await UnreadMessageRepository.find_by_conversation(userId, conversationId)

        if existing:
            existing.unreadCount = 0
            existing.lastReadTime = existing.updateAt
            existing.update_timestamp()
            await existing.replace()
            logger.debug(f"清除未读: userId={userId}, conversationId={conversationId}")
            return True

        return False

    @staticmethod
    async def batch_clear_by_user(
        userId: str,
        conversationType: Optional[int] = None,
    ) -> int:
        """
        批量清除用户所有会话的未读计数

        Args:
            userId: 用户ID
            conversationType: 可选，只清除指定类型的会话

        Returns:
            清除的记录数
        """
        query = {"userId": userId}
        if conversationType is not None:
            query["conversationType"] = conversationType

        unread_list = await UnreadMessage.find(query).to_list()
        count = 0

        for unread in unread_list:
            if unread.unreadCount > 0:
                unread.unreadCount = 0
                unread.lastReadTime = unread.updateAt
                unread.update_timestamp()
                await unread.replace()
                count += 1

        logger.debug(f"批量清除未读: userId={userId}, count={count}")
        return count

    @staticmethod
    async def delete_by_conversation(
        userId: str,
        conversationId: str,
    ) -> bool:
        """
        删除指定会话的未读记录

        Args:
            userId: 用户ID
            conversationId: 会话ID

        Returns:
            是否删除成功
        """
        existing = await UnreadMessageRepository.find_by_conversation(userId, conversationId)

        if existing:
            await existing.delete()
            logger.debug(f"删除未读记录: userId={userId}, conversationId={conversationId}")
            return True

        return False

    @staticmethod
    async def get_total_unread(userId: str) -> int:
        """
        获取用户的总未读数量

        Args:
            userId: 用户ID

        Returns:
            总未读数量
        """
        unread_list = await UnreadMessageRepository.find_by_user_id(userId)
        total = sum(unread.unreadCount for unread in unread_list)
        return total
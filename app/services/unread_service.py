"""
未读消息计数服务层

处理未读消息计数相关的业务逻辑
"""
import logging
from typing import List

from app.repository.unread_message_repository import UnreadMessageRepository
from app.repository.user_repository import UserRepository
from app.repository.group_repository import GroupRepository

logger = logging.getLogger(__name__)

# 聊天类型常量
CHAT_TYPE_GROUP = 1  # 群聊
CHAT_TYPE_PRIVATE = 2  # 私聊


class UnreadService:
    """
    未读消息计数服务类
    """

    @staticmethod
    async def get_list(
        userId: str,
        conversationType: int = None,
    ) -> dict:
        """
        获取用户的未读消息列表

        Args:
            userId: 用户ID
            conversationType: 可选，过滤会话类型

        Returns:
            未读消息列表响应
        """
        unread_list = await UnreadMessageRepository.find_by_user_id(userId, conversationType)

        # 计算总未读数
        total = sum(unread.unreadCount for unread in unread_list)

        # 转换为响应格式
        data_list = [
            {
                "conversationId": unread.conversationId,
                "conversationType": unread.conversationType,
                "unreadCount": unread.unreadCount,
                "updateAt": unread.updateAt,
            }
            for unread in unread_list
        ]

        return {
            "total": total,
            "list": data_list,
        }

    @staticmethod
    async def clear(
        userId: str,
        conversationId: str,
    ) -> None:
        """
        清除指定会话的未读计数

        Args:
            userId: 用户ID
            conversationId: 会话ID
        """
        await UnreadMessageRepository.clear(userId, conversationId)
        logger.info(f"清除未读计数: userId={userId}, conversationId={conversationId}")

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
        newCount = await UnreadMessageRepository.increment(
            userId, conversationId, conversationType, delta
        )
        logger.info(f"增加未读计数: userId={userId}, conversationId={conversationId}, delta={delta}, newCount={newCount}")
        return newCount

    @staticmethod
    async def increment_for_conversation(
        conversationId: str,
        sendId: str,
        chatType: int,
    ) -> List[dict]:
        """
        为会话中的所有接收者增加未读计数

        Args:
            conversationId: 会话ID
            sendId: 发送者ID（不增加未读）
            chatType: 聊天类型（1=群组，2=私聊）

        Returns:
            更新的用户未读计数列表
        """
        updates = []

        if chatType == CHAT_TYPE_PRIVATE:
            # 私聊：解析会话ID获取接收者ID
            recvId = UnreadService._extract_recv_id_from_private_conversation(
                conversationId, sendId
            )
            if recvId:
                newCount = await UnreadService.increment(
                    recvId, conversationId, CHAT_TYPE_PRIVATE, 1
                )
                updates.append({
                    "userId": recvId,
                    "conversationId": conversationId,
                    "unreadCount": newCount,
                })
                logger.info(f"私聊未读更新: recvId={recvId}, conversationId={conversationId}, count={newCount}")

        elif chatType == CHAT_TYPE_GROUP:
            # 群聊：获取所有成员，排除发送者
            group = await GroupRepository.find_by_id(conversationId)
            if group:
                for memberId in group.memberIds:
                    if memberId != sendId:
                        newCount = await UnreadService.increment(
                            memberId, conversationId, CHAT_TYPE_GROUP, 1
                        )
                        updates.append({
                            "userId": memberId,
                            "conversationId": conversationId,
                            "unreadCount": newCount,
                        })
                logger.info(f"群聊未读更新: groupId={conversationId}, membersUpdated={len(updates)}")

        return updates

    @staticmethod
    def _extract_recv_id_from_private_conversation(
        conversationId: str,
        sendId: str,
    ) -> str:
        """
        从私聊会话ID中提取接收者ID

        私聊会话ID格式：private_{min(id1, id2)}_{max(id1, id2)}

        Args:
            conversationId: 会话ID
            sendId: 发送者ID

        Returns:
            接收者ID
        """
        if not conversationId.startswith("private_"):
            return ""

        # 解析会话ID获取两个用户ID
        parts = conversationId.split("_")
        if len(parts) != 3:
            return ""

        user1Id = parts[1]
        user2Id = parts[2]

        # 返回不是发送者的那个ID
        return user2Id if user1Id == sendId else user1Id

    @staticmethod
    async def batch_clear_by_user(
        userId: str,
        conversationType: int = None,
    ) -> int:
        """
        批量清除用户所有会话的未读计数

        Args:
            userId: 用户ID
            conversationType: 可选，只清除指定类型的会话

        Returns:
            清除的记录数
        """
        count = await UnreadMessageRepository.batch_clear_by_user(userId, conversationType)
        logger.info(f"批量清除未读: userId={userId}, count={count}")
        return count
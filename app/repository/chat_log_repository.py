"""
聊天记录数据访问层

提供聊天记录相关的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.chat_log import ChatLog

logger = logging.getLogger(__name__)


class ChatLogRepository:
    """
    聊天记录数据访问层

    封装所有聊天记录相关的数据库操作
    """

    @staticmethod
    async def create(chat_log: ChatLog) -> ChatLog:
        """
        创建聊天记录

        Args:
            chat_log: ChatLog 实体对象

        Returns:
            创建后的 ChatLog 对象
        """
        await chat_log.insert()
        logger.info(f"聊天记录创建成功: conversationId={chat_log.conversationId}")
        return chat_log

    @staticmethod
    async def find_by_id(chat_log_id: str) -> Optional[ChatLog]:
        """
        根据 ID 查询聊天记录

        Args:
            chat_log_id: 聊天记录 ID

        Returns:
            ChatLog 对象或 None
        """
        return await ChatLog.get(PydanticObjectId(chat_log_id))

    @staticmethod
    async def delete(chat_log_id: str) -> bool:
        """
        删除聊天记录

        Args:
            chat_log_id: 聊天记录 ID

        Returns:
            是否删除成功
        """
        chat_log = await ChatLogRepository.find_by_id(chat_log_id)
        if not chat_log:
            return False
        await chat_log.delete()
        logger.info(f"聊天记录删除成功: id={chat_log_id}")
        return True

    @staticmethod
    async def find_by_conversation_id(
        conversation_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ChatLog], int]:
        """
        根据会话ID分页查询聊天记录

        Args:
            conversation_id: 会话ID
            page: 页码
            page_size: 每页数量

        Returns:
            (聊天记录列表, 总数)
        """
        skip = (page - 1) * page_size
        query = ChatLog.find(ChatLog.conversationId == conversation_id)
        total = await query.count()
        chat_logs = await query.skip(skip).limit(page_size).sort("-sendTime").to_list()
        return chat_logs, total

    @staticmethod
    async def find_by_send_id(
        send_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ChatLog], int]:
        """
        根据发送者ID分页查询聊天记录

        Args:
            send_id: 发送者ID
            page: 页码
            page_size: 每页数量

        Returns:
            (聊天记录列表, 总数)
        """
        skip = (page - 1) * page_size
        query = ChatLog.find(ChatLog.sendId == send_id)
        total = await query.count()
        chat_logs = await query.skip(skip).limit(page_size).sort("-sendTime").to_list()
        return chat_logs, total

    @staticmethod
    async def find_by_conditions(
        conversation_id: Optional[str] = None,
        send_id: Optional[str] = None,
        chat_type: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ChatLog], int]:
        """
        根据条件分页查询聊天记录

        Args:
            conversation_id: 会话ID
            send_id: 发送者ID
            chat_type: 聊天类型
            start_time: 开始时间戳
            end_time: 结束时间戳
            page: 页码
            page_size: 每页数量

        Returns:
            (聊天记录列表, 总数)
        """
        skip = (page - 1) * page_size

        # 构建查询条件
        conditions = []
        if conversation_id:
            conditions.append(ChatLog.conversationId == conversation_id)
        if send_id:
            conditions.append(ChatLog.sendId == send_id)
        if chat_type is not None:
            conditions.append(ChatLog.chatType == chat_type)
        if start_time is not None:
            conditions.append(ChatLog.sendTime >= start_time)
        if end_time is not None:
            conditions.append(ChatLog.sendTime <= end_time)

        query = ChatLog.find(*conditions) if conditions else ChatLog.find()
        total = await query.count()
        chat_logs = await query.skip(skip).limit(page_size).sort("-sendTime").to_list()
        return chat_logs, total
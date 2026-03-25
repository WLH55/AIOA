"""
聊天记录服务层

处理聊天记录相关的业务逻辑
"""
import logging
import time
from typing import List, Set, Optional

from app.config.exceptions import ResourceNotFoundException
from app.models.chat_log import ChatLog
from app.models.user import User
from app.repository.chat_log_repository import ChatLogRepository
from app.repository.user_repository import UserRepository
from app.dto.chat_log.chat_log_request import ChatLogRequest, ChatLogListRequest
from app.dto.chat_log.chat_log_response import ChatLogResponse, ChatLogListResponse

logger = logging.getLogger(__name__)

# 系统消息的特殊发送者ID
SYSTEM_SENDER_ID = "system"
SYSTEM_SENDER_NAME = "系统"


class ChatLogService:
    """
    聊天记录服务类

    提供聊天记录 CRUD、查询等业务逻辑
    """

    @staticmethod
    async def info(chat_log_id: str) -> ChatLogResponse:
        """
        获取聊天记录详情

        Args:
            chat_log_id: 聊天记录ID

        Returns:
            聊天记录详情响应 DTO

        Raises:
            ResourceNotFoundException: 聊天记录不存在
        """
        chat_log = await ChatLogRepository.find_by_id(chat_log_id)
        if not chat_log:
            raise ResourceNotFoundException("聊天记录不存在")

        # 获取发送者名称（系统消息特殊处理）
        if chat_log.sendId == SYSTEM_SENDER_ID:
            send_name = SYSTEM_SENDER_NAME
        else:
            send_user = await UserRepository.find_by_id(chat_log.sendId)
            send_name = send_user.name if send_user else ""

        # 获取接收者名称
        recv_name = ""
        if chat_log.recvId:
            recv_user = await UserRepository.find_by_id(chat_log.recvId)
            recv_name = recv_user.name if recv_user else ""

        return ChatLogResponse(
            id=str(chat_log.id),
            conversationId=chat_log.conversationId,
            sendId=chat_log.sendId,
            sendName=send_name,
            recvId=chat_log.recvId,
            recvName=recv_name,
            chatType=chat_log.chatType,
            msgContent=chat_log.msgContent,
            sendTime=chat_log.sendTime,
            createAt=chat_log.createAt,
        )

    @staticmethod
    async def create(request: ChatLogRequest) -> str:
        """
        创建聊天记录

        Args:
            request: 聊天记录请求 DTO

        Returns:
            创建的聊天记录ID
        """
        logger.info(f"创建聊天记录: conversationId={request.conversationId}")

        current_time = int(time.time() * 1000)

        chat_log = ChatLog(
            conversationId=request.conversationId,
            sendId=request.sendId,
            recvId=request.recvId,
            chatType=request.chatType,
            msgContent=request.msgContent,
            sendTime=current_time,
        )

        saved = await ChatLogRepository.create(chat_log)
        logger.info(f"创建聊天记录成功: id={saved.id}")

        return str(saved.id)

    @staticmethod
    async def list(request: ChatLogListRequest) -> ChatLogListResponse:
        """
        聊天记录列表查询

        Args:
            request: 聊天记录列表请求 DTO

        Returns:
            聊天记录列表响应 DTO
        """
        logger.info(f"聊天记录列表查询: page={request.page}, count={request.count}")

        chat_logs, total = await ChatLogRepository.find_by_conditions(
            conversation_id=request.conversationId,
            send_id=request.sendId,
            chat_type=request.chatType,
            start_time=request.startTime,
            end_time=request.endTime,
            page=request.page,
            page_size=request.count,
        )

        # 收集所有用户ID（排除系统消息的特殊ID）
        user_ids: Set[str] = set()
        for chat_log in chat_logs:
            if chat_log.sendId != SYSTEM_SENDER_ID:
                user_ids.add(chat_log.sendId)
            if chat_log.recvId and chat_log.recvId != SYSTEM_SENDER_ID:
                user_ids.add(chat_log.recvId)

        # 批量查询用户信息
        users = await UserRepository.find_by_ids(list(user_ids))
        user_map = {str(user.id): user for user in users}

        # 构建响应列表
        data: List[ChatLogResponse] = []
        for chat_log in chat_logs:
            # 系统消息特殊处理
            if chat_log.sendId == SYSTEM_SENDER_ID:
                send_name = SYSTEM_SENDER_NAME
            else:
                send_user = user_map.get(chat_log.sendId)
                send_name = send_user.name if send_user else ""

            recv_name = ""
            if chat_log.recvId:
                if chat_log.recvId == SYSTEM_SENDER_ID:
                    recv_name = SYSTEM_SENDER_NAME
                else:
                    recv_user = user_map.get(chat_log.recvId)
                    recv_name = recv_user.name if recv_user else ""

            data.append(ChatLogResponse(
                id=str(chat_log.id),
                conversationId=chat_log.conversationId,
                sendId=chat_log.sendId,
                sendName=send_name,
                recvId=chat_log.recvId,
                recvName=recv_name,
                chatType=chat_log.chatType,
                msgContent=chat_log.msgContent,
                sendTime=chat_log.sendTime,
                createAt=chat_log.createAt,
            ))

        return ChatLogListResponse(count=total, data=data)

    @staticmethod
    async def list_by_conversation(
        conversation_id: str,
        page: int = 1,
        count: int = 20
    ) -> ChatLogListResponse:
        """
        按会话查询聊天记录

        Args:
            conversation_id: 会话ID
            page: 页码
            count: 每页数量

        Returns:
            聊天记录列表响应 DTO
        """
        logger.info(f"按会话查询聊天记录: conversationId={conversation_id}")

        chat_logs, total = await ChatLogRepository.find_by_conversation_id(
            conversation_id, page, count
        )

        # 收集所有用户ID（排除系统消息的特殊ID）
        user_ids: Set[str] = set()
        for chat_log in chat_logs:
            if chat_log.sendId != SYSTEM_SENDER_ID:
                user_ids.add(chat_log.sendId)

        # 批量查询用户信息
        users = await UserRepository.find_by_ids(list(user_ids))
        user_map = {str(user.id): user for user in users}

        # 构建响应列表
        data: List[ChatLogResponse] = []
        for chat_log in chat_logs:
            # 系统消息特殊处理
            if chat_log.sendId == SYSTEM_SENDER_ID:
                send_name = SYSTEM_SENDER_NAME
            else:
                send_user = user_map.get(chat_log.sendId)
                send_name = send_user.name if send_user else ""

            data.append(ChatLogResponse(
                id=str(chat_log.id),
                conversationId=chat_log.conversationId,
                sendId=chat_log.sendId,
                sendName=send_name,
                recvId=chat_log.recvId,
                chatType=chat_log.chatType,
                msgContent=chat_log.msgContent,
                sendTime=chat_log.sendTime,
                createAt=chat_log.createAt,
            ))

        return ChatLogListResponse(count=total, data=data)
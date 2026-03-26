"""
聊天消息处理服务

处理 WebSocket 聊天消息的业务逻辑，包括私聊和群聊
"""
import logging
import time

from app.config.exceptions import BusinessValidationException, ResourceNotFoundException
from app.dto.ws.message import ChatMessage
from app.models.chat_log import ChatLog
from app.models.user import User
from app.repository.chat_log_repository import ChatLogRepository
from app.repository.group_repository import GroupRepository
from app.repository.user_repository import UserRepository
from app.services.ws_manager import ws_manager
from app.services.unread_service import UnreadService

logger = logging.getLogger(__name__)

# 聊天类型常量
CHAT_TYPE_GROUP = 1  # 群聊
CHAT_TYPE_PRIVATE = 2  # 私聊

# 内容类型常量
CONTENT_TYPE_TEXT = 1  # 文字
CONTENT_TYPE_IMAGE = 2  # 图片


class ChatService:
    """
    聊天消息服务类

    处理私聊和群聊消息的发送、转发和持久化
    """

    @staticmethod
    async def handle_message(message: ChatMessage, current_user: User) -> dict:
        """
        处理聊天消息

        Args:
            message: 聊天消息 DTO
            current_user: 当前发送用户

        Returns:
            响应消息字典

        Raises:
            BusinessValidationException: 业务验证失败
            ResourceNotFoundException: 资源不存在
        """
        # 验证消息内容
        if not message.content or not message.content.strip():
            raise BusinessValidationException("消息内容不能为空")

        send_id = str(current_user.id)
        current_time = int(time.time() * 1000)

        # 根据聊天类型处理
        if message.chatType == CHAT_TYPE_PRIVATE:
            # 私聊消息
            return await ChatService._handle_private_message(
                send_id=send_id,
                recv_id=message.recvId,
                content=message.content,
                content_type=message.contentType,
                conversation_id=message.conversationId,
                current_time=current_time,
            )

        elif message.chatType == CHAT_TYPE_GROUP:
            # 群聊消息
            return await ChatService._handle_group_message(
                send_id=send_id,
                conversation_id=message.conversationId,
                content=message.content,
                content_type=message.contentType,
                current_time=current_time,
            )

        else:
            raise BusinessValidationException(f"无效的消息类型: {message.chatType}")

    @staticmethod
    def generate_conversation_id(user1_id: str, user2_id: str) -> str:
        """
        生成私聊会话ID

        规则：private_{min(userId1, userId2)}_{max(userId1, userId2)}
        确保同一对用户的会话ID唯一

        Args:
            user1_id: 用户1 ID
            user2_id: 用户2 ID

        Returns:
            会话ID

        Raises:
            BusinessValidationException: 不能给自己发消息
        """
        if user1_id == user2_id:
            raise BusinessValidationException("不能给自己发消息")

        # 按 ID 字典序排序，确保唯一性
        sorted_ids = sorted([user1_id, user2_id])
        return f"private_{sorted_ids[0]}_{sorted_ids[1]}"

    @staticmethod
    async def _handle_private_message(
        send_id: str,
        recv_id: str,
        content: str,
        content_type: int,
        conversation_id: str,
        current_time: int,
    ) -> dict:
        """
        处理私聊消息

        Args:
            send_id: 发送者 ID
            recv_id: 接收者 ID
            content: 消息内容
            content_type: 内容类型
            conversation_id: 会话 ID（可为空，自动生成）
            current_time: 当前时间戳

        Returns:
            响应消息字典

        Raises:
            ResourceNotFoundException: 接收者不存在
            BusinessValidationException: 业务验证失败
        """
        logger.info(
            f"[私聊处理] 开始处理: sendId={send_id}, recvId={recv_id}, "
            f"conversationId={conversation_id}, content={content}"
        )
        # 验证接收者
        if not recv_id:
            raise BusinessValidationException("私聊消息必须指定接收者")

        # 验证用户 ID 长度（MongoDB ObjectId 应该是 24 位）
        if len(recv_id) != 24:
            logger.error(f"[私聊处理] 接收者ID长度异常: recvId={recv_id}, 长度={len(recv_id)}")
            raise BusinessValidationException(f"接收者ID格式错误: {recv_id}")

        if len(send_id) != 24:
            logger.error(f"[私聊处理] 发送者ID长度异常: sendId={send_id}, 长度={len(send_id)}")
            raise BusinessValidationException(f"发送者ID格式错误: {send_id}")

        logger.info(f"[私聊处理] 发送者ID: sendId={send_id}, 接收者ID: recvId")

        # 查询接收者是否存在
        recv_user = await UserRepository.find_by_id(recv_id)
        if not recv_user:
            raise ResourceNotFoundException("接收者不存在")

        # 生成会话 ID
        if not conversation_id:
            conversation_id = ChatService.generate_conversation_id(send_id, recv_id)

        # 检查接收者是否在线
        is_online = ws_manager.is_user_online(recv_id)

        # 保存消息到数据库
        chat_log = ChatLog(
            conversationId=conversation_id,
            sendId=send_id,
            recvId=recv_id,
            chatType=CHAT_TYPE_PRIVATE,
            msgContent=content,
            sendTime=current_time,
        )
        await ChatLogRepository.create(chat_log)

        logger.info(
            f"私聊消息已保存: sendId={send_id}, recvId={recv_id}, "
            f"conversationId={conversation_id}, isOnline={is_online}"
        )

        # 增加接收者未读计数
        try:
            await UnreadService.increment(
                userId=recv_id,
                conversationId=conversation_id,
                conversationType=CHAT_TYPE_PRIVATE,
                delta=1,
            )
            logger.info(f"已增加接收者未读计数: recvId={recv_id}, conversationId={conversation_id}")
        except Exception as e:
            logger.error(f"增加未读计数失败: {e}")

        # 构建响应
        response = {
            "type": "message",
            "conversationId": conversation_id,
            "sendId": send_id,
            "recvId": recv_id,
            "chatType": CHAT_TYPE_PRIVATE,
            "content": content,
            "contentType": content_type,
            "sendTime": current_time,
        }

        logger.info(
            f"构建私聊响应: sendId={send_id}, recvId={recv_id}, "
            f"conversationId={conversation_id}, content={content}"
        )

        # 如果接收者在线，转发消息
        if is_online:
            await ws_manager.send_to_user(recv_id, response)
            response["status"] = "sent"
            logger.info(f"私聊消息已转发给接收者: recvId={recv_id}")
        else:
            response["status"] = "offline"
            logger.info(f"接收者不在线: recvId={recv_id}")

        return response

    @staticmethod
    async def _handle_group_message(
        send_id: str,
        conversation_id: str,
        content: str,
        content_type: int,
        current_time: int,
    ) -> dict:
        """
        处理群聊消息

        Args:
            send_id: 发送者 ID
            conversation_id: 群聊 ID
            content: 消息内容
            content_type: 内容类型
            current_time: 当前时间戳

        Returns:
            响应消息字典

        Raises:
            ResourceNotFoundException: 群聊不存在
            BusinessValidationException: 业务验证失败
        """
        # 验证群聊 ID
        if not conversation_id:
            raise BusinessValidationException("群聊消息必须指定群聊 ID")

        # 查询群聊信息
        group = await GroupRepository.find_by_id(conversation_id)
        if not group:
            raise ResourceNotFoundException("群聊不存在")

        # 验证发送者是否为群成员
        if send_id not in group.memberIds:
            raise BusinessValidationException("不是群成员，无法发送消息")

        # 保存消息到数据库（群聊 recvId 为空）
        chat_log = ChatLog(
            conversationId=conversation_id,
            sendId=send_id,
            recvId=None,  # 群聊没有单个接收者
            chatType=CHAT_TYPE_GROUP,
            msgContent=content,
            sendTime=current_time,
        )
        await ChatLogRepository.create(chat_log)

        logger.info(
            f"群聊消息已保存: sendId={send_id}, groupId={conversation_id}, "
            f"memberCount={len(group.memberIds)}"
        )

        # 增加所有成员（除发送者）未读计数
        try:
            await UnreadService.increment_for_conversation(
                conversationId=conversation_id,
                sendId=send_id,
                chatType=CHAT_TYPE_GROUP,
            )
            logger.info(f"已增加群成员未读计数: groupId={conversation_id}, sendId={send_id}")
        except Exception as e:
            logger.error(f"增加未读计数失败: {e}")

        # 构建广播消息
        broadcast_message = {
            "type": "message",
            "conversationId": conversation_id,
            "sendId": send_id,
            "recvId": "",
            "chatType": CHAT_TYPE_GROUP,
            "content": content,
            "contentType": content_type,
            "sendTime": current_time,
        }

        # 广播给群成员（排除发送者）
        await ws_manager.broadcast(
            broadcast_message,
            exclude={send_id}  # 不发送给发送者
        )

        logger.info(f"群聊消息已广播给群成员: groupId={conversation_id}")

        # 返回给发送者的确认
        return {
            **broadcast_message,
            "status": "sent",
        }

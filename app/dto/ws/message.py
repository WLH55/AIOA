"""
WebSocket 消息 DTO

定义客户端发送的消息类型和数据结构
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """
    WebSocket 消息类型枚举
    """
    # 客户端 -> 服务端
    CHAT = "chat"           # 聊天消息
    PONG = "pong"           # 心跳响应
    CLOSE = "close"         # 关闭连接

    # 服务端 -> 客户端
    CONNECTED = "connected" # 连接成功
    KICKED = "kicked"       # 被踢下线
    PING = "ping"           # 心跳请求
    MESSAGE = "message"     # AI 响应消息
    ERROR = "error"         # 错误消息


class WebSocketMessage(BaseModel):
    """
    WebSocket 消息基类
    """
    type: MessageType = Field(..., description="消息类型")


class ChatMessage(BaseModel):
    """
    聊天消息

    客户端发送给服务端的聊天消息
    """
    type: MessageType = Field(default=MessageType.CHAT, description="消息类型")
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="消息内容"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="会话 ID（可选，用于多轮对话）"
    )

    def get_or_create_conversation_id(self) -> str:
        """
        获取或创建会话 ID

        Returns:
            str: 会话 ID
        """
        if not self.conversation_id:
            self.conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        return self.conversation_id


class PongMessage(BaseModel):
    """
    心跳响应消息

    客户端响应服务端的 ping
    """
    type: MessageType = Field(default=MessageType.PONG, description="消息类型")
    timestamp: Optional[str] = Field(
        default=None,
        description="时间戳"
    )


class CloseMessage(BaseModel):
    """
    关闭连接消息

    客户端主动请求关闭连接
    """
    type: MessageType = Field(default=MessageType.CLOSE, description="消息类型")
    reason: Optional[str] = Field(
        default=None,
        description="关闭原因"
    )
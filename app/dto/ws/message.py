"""
WebSocket 消息 DTO

定义客户端发送的消息类型和数据结构
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """
    WebSocket 消息类型枚举
    """
    CHAT = "chat"
    PONG = "pong"
    CLOSE = "close"
    CONNECTED = "connected"
    KICKED = "kicked"
    PING = "ping"
    MESSAGE = "message"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """
    WebSocket 消息基类
    """
    type: MessageType = Field(..., description="消息类型")


class GroupInfo(BaseModel):
    """
    群组信息
    """
    groupId: str = Field(..., description="群组ID")
    groupName: str = Field(..., description="群组名称")
    memberIds: List[str] = Field(default_factory=list, description="成员ID列表")
    creatorId: str = Field(..., description="创建者ID")


class ChatMessage(BaseModel):
    """
    聊天消息

    客户端发送给服务端的聊天消息
    与前端 WsMessage 结构保持一致
    """
    type: MessageType = Field(default=MessageType.CHAT, description="消息类型")
    conversationId: str = Field(..., description="会话ID（群聊为群ID，私聊为两个用户ID组合）")
    recvId: Optional[str] = Field(None, description="接收者ID（群聊时为空）")
    sendId: str = Field(..., description="发送者ID")
    chatType: int = Field(default=1, description="聊天类型(1-群聊, 2-私聊)")
    content: str = Field(..., description="消息内容")
    contentType: int = Field(default=1, description="内容类型(1-文字, 2-图片, 3-表情包)")
    systemType: Optional[str] = Field(None, description="系统消息类型(group_create/group_dismiss)")
    groupInfo: Optional[GroupInfo] = Field(None, description="群组信息")

    def get_or_create_conversation_id(self) -> str:
        """获取或创建会话 ID"""
        if not self.conversationId:
            self.conversationId = f"conv_{uuid.uuid4().hex[:12]}"
        return self.conversationId


class PingMessage(BaseModel):
    """
    心跳请求消息
    """
    type: MessageType = Field(default=MessageType.PING, description="消息类型")
    timestamp: Optional[str] = Field(None, description="时间戳")


class PongMessage(BaseModel):
    """
    心跳响应消息
    """
    type: MessageType = Field(default=MessageType.PONG, description="消息类型")
    timestamp: Optional[str] = Field(None, description="时间戳")


class CloseMessage(BaseModel):
    """
    关闭连接消息
    """
    type: MessageType = Field(default=MessageType.CLOSE, description="消息类型")
    reason: Optional[str] = Field(None, description="关闭原因")
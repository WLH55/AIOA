"""
WebSocket 响应 DTO

定义服务端发送的响应消息类型和数据结构
"""
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from app.dto.ws.message import MessageType


class WebSocketResponse(BaseModel):
    """
    WebSocket 响应基类
    """
    type: MessageType = Field(..., description="消息类型")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="时间戳"
    )


class ConnectedResponse(BaseModel):
    """
    连接成功响应

    服务端在 WebSocket 连接建立后发送
    """
    type: MessageType = Field(default=MessageType.CONNECTED, description="消息类型")
    user_id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    session_id: str = Field(..., description="会话 ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="时间戳"
    )


class KickedResponse(BaseModel):
    """
    被踢下线响应

    当用户在其他设备登录时发送给旧连接
    """
    type: MessageType = Field(default=MessageType.KICKED, description="消息类型")
    reason: str = Field(..., description="踢下线原因")
    message: str = Field(..., description="提示消息")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="时间戳"
    )


class ErrorResponse(BaseModel):
    """
    错误响应

    当发生错误时发送
    """
    type: MessageType = Field(default=MessageType.ERROR, description="消息类型")
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: Optional[Any] = Field(
        default=None,
        description="错误详情"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="时间戳"
    )


class MessageResponse(BaseModel):
    """
    AI 消息响应

    服务端发送 AI 响应消息
    """
    type: MessageType = Field(default=MessageType.MESSAGE, description="消息类型")
    content: str = Field(..., description="消息内容")
    conversation_id: str = Field(..., description="会话 ID")
    message_id: str = Field(..., description="消息 ID")
    is_final: bool = Field(
        default=False,
        description="是否为最终消息（流式传输时使用）"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="时间戳"
    )


class PingResponse(BaseModel):
    """
    心跳请求

    服务端发送给客户端的心跳
    """
    type: MessageType = Field(default=MessageType.PING, description="消息类型")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="时间戳"
    )
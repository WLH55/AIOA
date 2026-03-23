"""
WebSocket DTO 包
"""
from app.dto.ws.message import (
    MessageType,
    WebSocketMessage,
    ChatMessage,
    PongMessage,
    CloseMessage,
)
from app.dto.ws.response import (
    WebSocketResponse,
    ConnectedResponse,
    KickedResponse,
    ErrorResponse,
)

__all__ = [
    # 消息类型
    "MessageType",
    "WebSocketMessage",
    "ChatMessage",
    "PongMessage",
    "CloseMessage",
    # 响应类型
    "WebSocketResponse",
    "ConnectedResponse",
    "KickedResponse",
    "ErrorResponse",
]
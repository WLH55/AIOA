"""
未读消息计数模型

存储用户每个会话的未读消息数量
"""
import logging
from typing import Optional
from pydantic import Field
from beanie import Document, Indexed

logger = logging.getLogger(__name__)


class UnreadMessage(Document):
    """
    未读消息计数模型

    用于跟踪用户在每个会话中的未读消息数量
    """
    userId: str = Field(..., description="用户ID")
    conversationId: str = Field(..., description="会话ID（私聊：private_abc，群组：group_xyz）")
    conversationType: int = Field(..., description="会话类型：1=群组，2=私聊")
    unreadCount: int = Field(default=0, description="未读消息数量")
    lastReadTime: Optional[int] = Field(None, description="最后阅读时间戳（毫秒）")

    class Settings:
        name = "unread_message"
        indexes = [
            "userId",
            "conversationId",
            "conversationType",
        ]
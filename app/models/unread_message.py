"""
未读消息计数模型

存储用户每个会话的未读消息数量
"""
import logging
import time
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

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        name = "unread_message"
        indexes = [
            "userId",
            "conversationId",
            "conversationType",
        ]

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)
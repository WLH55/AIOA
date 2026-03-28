"""
聊天记录实体模型

使用 Beanie ODM 定义 MongoDB Document
"""
import time
from typing import Optional
from pydantic import Field
from beanie import Document, Indexed


class ChatLog(Document):
    """
    聊天记录文档模型

    Attributes:
        conversationId: 会话ID（群聊：群ID，私聊：双方用户ID生成的唯一标识）
        sendId: 发送者用户ID
        recvId: 接收者用户ID（群聊时为空）
        chatType: 聊天类型（1-群聊，2-私聊）
        msgContent: 消息内容
        sendTime: 发送时间戳
        createAt: 创建时间戳
        updateAt: 更新时间戳
    """

    # 会话信息
    conversationId: Indexed(str) = Field(..., description="会话ID")
    sendId: str = Field(..., description="发送者用户ID")
    recvId: Optional[str] = Field(None, description="接收者用户ID(群聊时为空)")

    # 消息信息
    chatType: int = Field(default=1, description="聊天类型(1-群聊, 2-私聊, 3-AI消息)")
    msgContent: str = Field(..., description="消息内容")
    sendTime: int = Field(default_factory=lambda: int(time.time() * 1000), description="发送时间戳")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "chat_log"
        indexes = [
            "conversationId",
        ]

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "conversationId": "conv123",
                "sendId": "user1",
                "recvId": "user2",
                "chatType": 2,
                "msgContent": "你好，请问有什么可以帮助你的？",
                "sendTime": 1704067200000,
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
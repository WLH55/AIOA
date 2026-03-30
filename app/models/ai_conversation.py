"""
AI 会话实体模型

使用 Beanie ODM 定义 MongoDB Document，管理用户的 AI 对话会话
"""
import time
from typing import Optional
from pydantic import Field
from beanie import Document, Indexed


class AiConversation(Document):
    """
    AI 会话文档模型

    Attributes:
        userId: 所属用户 ID
        title: 会话标题（首条消息自动生成，最长 50 字符）
        status: 状态（1-活跃，2-已删除）
        createdAt: 创建时间戳（毫秒）
        updatedAt: 最后更新时间戳（毫秒）
    """

    userId: Indexed(str) = Field(..., description="所属用户ID")
    title: Optional[str] = Field(None, max_length=50, description="会话标题")
    status: int = Field(default=1, description="状态: 1-活跃, 2-已删除")
    createdAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updatedAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="最后更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "ai_conversation"
        indexes = [
            "userId",
            "updatedAt",
            [("userId", 1), ("status", 1)],
        ]

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updatedAt = int(time.time() * 1000)

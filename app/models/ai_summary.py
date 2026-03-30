"""
AI 摘要实体模型

使用 Beanie ODM 定义 MongoDB Document，存储 AI 对话的增量摘要
"""
import time
from pydantic import Field
from beanie import Document, Indexed


class AiSummary(Document):
    """
    AI 摘要文档模型

    一个会话只有一条摘要记录，通过增量方式更新

    Attributes:
        conversationId: 关联会话 ID（唯一）
        summary: 摘要内容
        charCount: 摘要生成时的对话字符数
        createdAt: 首次创建时间戳（毫秒）
        updatedAt: 最后更新时间戳（毫秒）
    """

    conversationId: Indexed(str, unique=True) = Field(..., description="关联会话ID")
    summary: str = Field(..., description="摘要内容")
    charCount: int = Field(default=0, description="摘要生成时的对话字符数")
    createdAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="首次创建时间戳")
    updatedAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="最后更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "ai_summary"
        indexes = [
            "conversationId",
        ]

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updatedAt = int(time.time() * 1000)

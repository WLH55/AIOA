"""
群组实体模型

使用 Beanie ODM 定义 MongoDB Document
"""
import time
from typing import Optional, List
from pydantic import Field
from beanie import Document, Indexed


class Group(Document):
    """
    群组文档模型

    Attributes:
        name: 群组名称
        avatar: 群头像URL
        ownerId: 群主ID
        memberIds: 成员ID列表
        status: 状态（1-正常，2-已解散）
        createAt: 创建时间戳
        updateAt: 更新时间戳
    """

    # 基本信息
    name: Indexed(str) = Field(..., min_length=1, max_length=50, description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")
    ownerId: str = Field(..., description="群主ID")
    memberIds: List[str] = Field(default_factory=list, description="成员ID列表")

    # 状态
    status: int = Field(default=1, description="状态(1-正常, 2-已解散)")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "group"
        indexes = [
            "name",
            "ownerId",
            "memberIds",  # 用于查询用户参与的群组
        ]

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "name": "产品研发讨论组",
                "avatar": "https://example.com/avatar.png",
                "ownerId": "user123",
                "memberIds": ["user123", "user456", "user789"],
                "status": 1,
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)

"""
用户实体模型

使用 Beanie ODM 定义 MongoDB Document
"""
import time
from typing import Optional
from pydantic import Field
from beanie import Document, Indexed


class User(Document):
    """
    用户文档模型

    Attributes:
        name: 用户名（唯一）
        password: 密码（BCrypt 加密）
        status: 状态（0-正常，1-禁用）
        isAdmin: 是否为管理员
        createAt: 创建时间戳
        updateAt: 更新时间戳
    """

    # 基本信息
    name: Indexed(str, unique=True) = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., description="密码(BCrypt加密)")

    # 状态与权限
    status: int = Field(default=1, description="状态(1-启用, 0-禁用)")
    isAdmin: bool = Field(default=False, description="是否为管理员")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "user"
        indexes = [
            "name",
        ]

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "name": "zhangsan",
                "password": "$2b$12$...",
                "status": 0,
                "isAdmin": False,
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
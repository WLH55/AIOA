"""
部门用户关联实体模型

使用 Beanie ODM 定义 MongoDB Document
处理用户与部门之间的多对多关系
"""
import time
from pydantic import Field
from beanie import Document, Indexed


class DepartmentUser(Document):
    """
    部门用户关联文档模型

    处理用户与部门之间的多对多关系

    Attributes:
        depId: 部门ID
        userId: 用户ID
        createAt: 创建时间戳
        updateAt: 更新时间戳
    """

    # 关联信息
    depId: Indexed(str) = Field(..., description="部门ID")
    userId: Indexed(str) = Field(..., description="用户ID")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "department_user"
        indexes = [
            "depId",
            "userId",
        ]

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "depId": "dept001",
                "userId": "user123",
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
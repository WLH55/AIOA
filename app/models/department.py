"""
部门实体模型

使用 Beanie ODM 定义 MongoDB Document
树形结构设计
"""
import time
from typing import Optional
from pydantic import Field
from beanie import Document


class Department(Document):
    """
    部门文档模型

    采用树形结构存储部门层级

    Attributes:
        name: 部门名称
        parentId: 父部门ID
        parentPath: 祖先路径（用冒号分隔的ID链）
        level: 部门层级
        leaderId: 部门负责人ID
        leader: 部门负责人姓名
        count: 部门人数
        createAt: 创建时间戳
        updateAt: 更新时间戳
    """

    # 基本信息
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")

    # 树形结构
    parentId: Optional[str] = Field(None, description="父部门ID")
    parentPath: Optional[str] = Field(None, description="祖先路径(用冒号分隔的ID链)")
    level: int = Field(default=1, description="部门层级")

    # 负责人信息
    leaderId: Optional[str] = Field(None, description="部门负责人ID")
    leader: Optional[str] = Field(None, description="部门负责人姓名")

    # 统计
    count: int = Field(default=0, description="部门人数")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "department"

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "name": "技术部",
                "parentId": "dept001",
                "parentPath": "root:dept001",
                "level": 2,
                "leaderId": "user123",
                "leader": "张三",
                "count": 50,
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
"""
待办事项实体模型

使用 Beanie ODM 定义 MongoDB Document
包含内嵌文档：UserTodo（执行人）、TodoRecord（操作记录）
"""
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from beanie import Document


# ==================== 内嵌文档 ====================

class UserTodo(BaseModel):
    """
    用户待办关联（内嵌文档）

    用于 Todo 实体中的 executes 字段
    """

    id: str = Field(..., description="唯一标识")
    userId: str = Field(..., description="用户ID")
    userName: str = Field(..., description="用户名")
    todoId: str = Field(..., description="待办ID")
    todoStatus: int = Field(default=1, description="待办状态")
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")


class TodoRecord(BaseModel):
    """
    待办事项操作记录（内嵌文档）

    用于 Todo 实体中的 records 字段
    """

    userId: str = Field(..., description="操作用户ID")
    userName: str = Field(..., description="操作用户名")
    content: str = Field(..., description="操作内容")
    image: Optional[str] = Field(None, description="操作相关图片")
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="操作时间戳")


# ==================== 主文档 ====================

class Todo(Document):
    """
    待办事项文档模型

    Attributes:
        creatorId: 创建者ID
        title: 待办标题
        deadlineAt: 截止时间戳
        desc: 待办描述
        records: 操作记录列表
        executes: 执行人列表
        todoStatus: 待办状态（1-待处理，2-进行中，3-已完成，4-已取消，5-已超时）
        createAt: 创建时间戳
        updateAt: 更新时间戳
    """

    # 基本信息
    creatorId: str = Field(..., description="创建者ID")
    title: str = Field(..., min_length=1, max_length=200, description="待办标题")
    deadlineAt: Optional[int] = Field(None, description="截止时间戳")
    desc: Optional[str] = Field(None, description="待办描述")

    # 内嵌文档
    records: List[TodoRecord] = Field(default_factory=list, description="操作记录列表")
    executes: List[UserTodo] = Field(default_factory=list, description="执行人列表")

    # 状态
    todoStatus: int = Field(default=1, description="待办状态(1-待处理, 2-进行中, 3-已完成, 4-已取消, 5-已超时)")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "todo"

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "creatorId": "user123",
                "title": "完成项目报告",
                "deadlineAt": 1704067200000,
                "desc": "需要在周五前完成Q4项目报告",
                "records": [],
                "executes": [],
                "todoStatus": 1,
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
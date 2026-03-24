"""
待办事项响应 DTO 模块

定义待办事项相关的响应数据结构
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class UserTodoResponse(BaseModel):
    """
    用户待办关联响应 DTO
    """

    id: Optional[str] = Field(None, description="唯一标识")
    user_id: str = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户名")
    todo_id: Optional[str] = Field(None, description="待办ID")
    todo_status: int = Field(default=1, description="待办状态")


class TodoRecordResponse(BaseModel):
    """
    待办操作记录响应 DTO
    """

    todo_id: Optional[str] = Field(None, description="待办ID")
    user_id: str = Field(..., description="操作用户ID")
    user_name: str = Field(..., description="操作用户名")
    content: str = Field(..., description="操作内容")
    image: Optional[str] = Field(None, description="操作相关图片")
    create_at: Optional[int] = Field(None, description="操作时间戳")


class TodoResponse(BaseModel):
    """
    待办事项响应 DTO

    用于列表展示
    """

    id: str = Field(..., description="待办ID")
    creator_id: str = Field(..., description="创建者ID")
    creator_name: str = Field(..., description="创建者名称")
    title: str = Field(..., description="待办标题")
    deadline_at: Optional[int] = Field(None, description="截止时间戳")
    desc: Optional[str] = Field(None, description="待办描述")
    status: int = Field(..., description="待办状态")
    todo_status: int = Field(..., description="待办状态")
    execute_ids: List[str] = Field(default_factory=list, description="执行人名称列表")
    create_at: Optional[int] = Field(None, description="创建时间戳")
    update_at: Optional[int] = Field(None, description="更新时间戳")


class TodoInfoResponse(BaseModel):
    """
    待办详情响应 DTO

    用于详情展示，包含完整的执行人和操作记录信息
    """

    id: str = Field(..., description="待办ID")
    creator_id: str = Field(..., description="创建者ID")
    creator_name: str = Field(..., description="创建者名称")
    title: str = Field(..., description="待办标题")
    deadline_at: Optional[int] = Field(None, description="截止时间戳")
    desc: Optional[str] = Field(None, description="待办描述")
    status: int = Field(..., description="待办状态")
    todo_status: int = Field(..., description="待办状态")
    execute_ids: List[UserTodoResponse] = Field(default_factory=list, description="执行人列表")
    records: List[TodoRecordResponse] = Field(default_factory=list, description="操作记录列表")


class TodoListResponse(BaseModel):
    """
    待办列表响应 DTO
    """

    count: int = Field(..., description="总数")
    data: List[TodoResponse] = Field(default_factory=list, description="待办列表")
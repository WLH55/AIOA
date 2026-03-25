"""
待办事项请求 DTO 模块

定义待办事项相关的请求参数
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class TodoRecordRequestDto(BaseModel):
    """
    待办操作记录请求 DTO

    用于创建待办操作记录
    """

    userId: str = Field(..., description="操作用户ID")
    userName: Optional[str] = Field(None, description="操作用户名")
    content: str = Field(..., description="操作内容")
    image: Optional[str] = Field(None, description="操作相关图片")


class UserTodoRequestDto(BaseModel):
    """
    用户待办关联请求 DTO

    用于指定待办执行人
    """

    id: Optional[str] = Field(None, description="唯一标识")
    userId: str = Field(..., description="用户ID")
    userName: Optional[str] = Field(None, description="用户名")
    todoStatus: int = Field(default=1, description="待办状态")


class TodoRequest(BaseModel):
    """
    待办事项请求 DTO

    用于创建和编辑待办事项
    """

    id: Optional[str] = Field(None, description="待办ID(编辑时需要)")
    title: str = Field(..., min_length=1, max_length=200, description="待办标题")
    deadlineAt: Optional[int] = Field(None, description="截止时间戳(毫秒)")
    desc: Optional[str] = Field(None, description="待办描述")
    status: Optional[int] = Field(None, description="待办状态")
    executeIds: Optional[List[str]] = Field(None, description="执行人ID列表")
    records: Optional[List[TodoRecordRequestDto]] = Field(None, description="操作记录列表")


class TodoListRequest(BaseModel):
    """
    待办列表请求 DTO

    用于查询待办列表
    """

    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=10, ge=1, le=100, description="每页数量")
    id: Optional[str] = Field(None, description="待办ID")
    userId: Optional[str] = Field(None, description="用户ID")
    startTime: Optional[int] = Field(None, description="开始时间戳(毫秒)")
    endTime: Optional[int] = Field(None, description="结束时间戳(毫秒)")


class FinishTodoRequest(BaseModel):
    """
    完成待办请求 DTO
    """

    userId: str = Field(..., description="完成用户ID")
    todoId: str = Field(..., description="待办ID")


class TodoRecordRequest(BaseModel):
    """
    创建操作记录请求 DTO
    """

    todoId: str = Field(..., description="待办ID")
    content: str = Field(..., description="操作内容")
    image: Optional[str] = Field(None, description="操作相关图片")
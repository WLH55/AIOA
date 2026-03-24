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

    user_id: str = Field(..., description="操作用户ID")
    user_name: Optional[str] = Field(None, description="操作用户名")
    content: str = Field(..., description="操作内容")
    image: Optional[str] = Field(None, description="操作相关图片")


class UserTodoRequestDto(BaseModel):
    """
    用户待办关联请求 DTO

    用于指定待办执行人
    """

    id: Optional[str] = Field(None, description="唯一标识")
    user_id: str = Field(..., description="用户ID")
    user_name: Optional[str] = Field(None, description="用户名")
    todo_status: int = Field(default=1, description="待办状态")


class TodoRequest(BaseModel):
    """
    待办事项请求 DTO

    用于创建和编辑待办事项
    """

    id: Optional[str] = Field(None, description="待办ID(编辑时需要)")
    title: str = Field(..., min_length=1, max_length=200, description="待办标题")
    deadline_at: Optional[int] = Field(None, description="截止时间戳(毫秒)")
    desc: Optional[str] = Field(None, description="待办描述")
    status: Optional[int] = Field(None, description="待办状态")
    execute_ids: Optional[List[str]] = Field(None, description="执行人ID列表")
    records: Optional[List[TodoRecordRequestDto]] = Field(None, description="操作记录列表")


class TodoListRequest(BaseModel):
    """
    待办列表请求 DTO

    用于查询待办列表
    """

    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=10, ge=1, le=100, description="每页数量")
    start_time: Optional[int] = Field(None, description="开始时间戳(毫秒)")
    end_time: Optional[int] = Field(None, description="结束时间戳(毫秒)")


class FinishTodoRequest(BaseModel):
    """
    完成待办请求 DTO
    """

    todo_id: str = Field(..., description="待办ID")
    user_id: str = Field(..., description="完成用户ID")


class TodoRecordRequest(BaseModel):
    """
    创建操作记录请求 DTO
    """

    todo_id: str = Field(..., description="待办ID")
    content: str = Field(..., description="操作内容")
    image: Optional[str] = Field(None, description="操作相关图片")
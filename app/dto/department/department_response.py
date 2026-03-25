"""
部门响应 DTO 模块

定义部门相关的响应数据结构
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class DepartmentUserResponse(BaseModel):
    """
    部门用户响应 DTO
    """

    id: Optional[str] = Field(None, description="关联ID")
    userId: str = Field(..., description="用户ID")
    depId: str = Field(..., description="部门ID")
    userName: Optional[str] = Field(None, description="用户名")


class DepartmentResponse(BaseModel):
    """
    部门响应 DTO

    包含树形结构支持
    """

    id: str = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    parentId: Optional[str] = Field(None, description="父部门ID")
    parentPath: Optional[str] = Field(None, description="父部门路径")
    level: int = Field(default=1, description="部门层级")
    leaderId: Optional[str] = Field(None, description="部门负责人ID")
    leader: Optional[str] = Field(None, description="部门负责人姓名")
    count: int = Field(default=0, description="部门人数")
    users: List[DepartmentUserResponse] = Field(default_factory=list, description="部门用户列表")
    child: Optional[List["DepartmentResponse"]] = Field(None, description="子部门列表")


class DepartmentTreeResponse(BaseModel):
    """
    部门树响应 DTO
    """

    child: List[DepartmentResponse] = Field(default_factory=list, description="部门树")
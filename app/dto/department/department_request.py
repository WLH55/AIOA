"""
部门请求 DTO 模块

定义部门相关的请求参数
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class DepartmentRequest(BaseModel):
    """
    部门请求 DTO

    用于创建和编辑部门
    """

    id: Optional[str] = Field(None, description="部门ID(编辑时需要)")
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    parent_id: Optional[str] = Field(None, description="父部门ID")
    level: Optional[int] = Field(None, ge=1, description="部门层级")
    leader_id: str = Field(..., description="部门负责人ID")


class SetDepartmentUsersRequest(BaseModel):
    """
    设置部门用户请求 DTO
    """

    dep_id: str = Field(..., description="部门ID")
    user_ids: List[str] = Field(default_factory=list, description="用户ID列表")


class AddDepartmentUserRequest(BaseModel):
    """
    添加部门员工请求 DTO
    """

    dep_id: str = Field(..., description="部门ID")
    user_id: str = Field(..., description="用户ID")


class RemoveDepartmentUserRequest(BaseModel):
    """
    删除部门员工请求 DTO
    """

    dep_id: str = Field(..., description="部门ID")
    user_id: str = Field(..., description="用户ID")
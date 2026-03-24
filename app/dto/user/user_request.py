"""
用户请求 DTO 模块

定义用户相关的请求参数
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class UserRequest(BaseModel):
    """
    用户请求

    用于创建和编辑用户
    """

    id: Optional[str] = Field(None, description="用户ID(编辑时需要)")
    name: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="密码")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态(0-正常, 1-禁用)")


class UserListRequest(BaseModel):
    """
    用户列表请求

    用于查询用户列表
    """

    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=10, ge=1, le=100, description="每页数量")
    name: Optional[str] = Field(None, description="用户名(模糊查询)")
    ids: Optional[List[str]] = Field(None, description="用户ID列表")


class UpdatePasswordRequest(BaseModel):
    """
    修改密码请求
    """

    id: str = Field(..., description="用户ID")
    old_pwd: str = Field(..., min_length=6, description="原密码")
    new_pwd: str = Field(..., min_length=6, description="新密码")

    @field_validator('new_pwd')
    @classmethod
    def validate_new_pwd(cls, v: str, info) -> str:
        """新密码不能与原密码相同"""
        old_pwd = info.data.get('old_pwd')
        if old_pwd and v == old_pwd:
            raise ValueError('新密码不能与原密码相同')
        return v
"""
用户登录 DTO

定义登录接口的请求和响应数据结构
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    用户登录请求 DTO

    Attributes:
        name: 用户名
        password: 密码
    """

    name: str = Field(
        ...,
        description="用户名",
        examples=["zhangsan"]
    )
    password: str = Field(
        ...,
        description="密码",
        examples=["Password123"]
    )


class LoginResponse(BaseModel):
    """
    用户登录响应 DTO

    扁平化结构，与前端字段保持一致
    """

    status: int = Field(default=0, description="状态(0-正常, 1-禁用)")
    id: str = Field(..., description="用户 ID")
    name: str = Field(..., description="用户名")
    token: str = Field(..., description="JWT Access Token")
    accessExpire: int = Field(..., description="Access Token 过期时间戳")
    refreshAfter: int = Field(..., description="建议刷新时间戳")
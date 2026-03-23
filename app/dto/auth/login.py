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


class UserInfo(BaseModel):
    """
    用户信息 DTO

    Attributes:
        user_id: 用户 ID
        name: 用户名
        status: 状态
        is_admin: 是否为管理员
    """

    user_id: str = Field(..., description="用户 ID")
    name: str = Field(..., description="用户名")
    status: int = Field(default=0, description="状态(0-正常, 1-禁用)")
    is_admin: bool = Field(default=False, description="是否为管理员")


class LoginResponse(BaseModel):
    """
    用户登录响应 DTO

    Attributes:
        access_token: JWT Access Token
        refresh_token: JWT Refresh Token
        token_type: Token 类型（固定为 "bearer"）
        expires_in: Access Token 过期时间（秒）
        user: 用户信息
    """

    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_in: int = Field(..., description="Access Token 过期时间（秒）")
    user: UserInfo = Field(..., description="用户信息")
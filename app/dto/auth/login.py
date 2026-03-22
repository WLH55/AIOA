"""
用户登录 DTO

定义登录接口的请求和响应数据结构
"""
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    """
    用户登录请求 DTO

    支持用户名或邮箱登录，两者至少提供一个

    Attributes:
        username: 用户名（与 email 二选一）
        email: 邮箱地址（与 username 二选一）
        password: 密码
    """

    username: Optional[str] = Field(
        None,
        description="用户名（与 email 二选一）",
        examples=["zhangsan"]
    )
    email: Optional[str] = Field(
        None,
        description="邮箱地址（与 username 二选一）",
        examples=["zhangsan@company.com"]
    )
    password: str = Field(
        ...,
        description="密码",
        examples=["Password123"]
    )

    @model_validator(mode="after")
    def validate_identifier(self) -> "LoginRequest":
        """
        验证至少提供了用户名或邮箱之一
        """
        if not self.username and not self.email:
            raise ValueError("必须提供用户名或邮箱")
        return self


class UserInfo(BaseModel):
    """
    用户信息 DTO

    Attributes:
        user_id: 用户 ID
        username: 用户名
        email: 邮箱地址
        full_name: 真实姓名
        roles: 角色列表
    """

    user_id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="真实姓名")
    roles: list[str] = Field(default_factory=lambda: ["user"], description="角色列表")


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
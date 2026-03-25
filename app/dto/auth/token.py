"""
Token 相关 DTO

定义 Token 刷新接口的请求和响应数据结构
"""
from pydantic import BaseModel, Field


class TokenRefreshRequest(BaseModel):
    """
    Token 刷新请求 DTO

    Attributes:
        refresh_token: JWT Refresh Token
    """

    refreshToken: str = Field(
        ...,
        description="JWT Refresh Token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )


class TokenRefreshResponse(BaseModel):
    """
    Token 刷新响应 DTO

    Attributes:
        access_token: 新的 JWT Access Token
        token_type: Token 类型（固定为 "bearer"）
        expires_in: Access Token 过期时间（秒）
    """

    accessToken: str = Field(..., description="新的 JWT Access Token")
    tokenType: str = Field(default="bearer", description="Token 类型")
    expiresIn: int = Field(..., description="Access Token 过期时间（秒）")
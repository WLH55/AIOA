"""
用户注册 DTO

定义注册接口的请求和响应数据结构
"""
import re
from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    """
    用户注册请求 DTO

    Attributes:
        name: 用户名（3-50字符，字母数字下划线）
        password: 密码（最小8位，必须包含字母和数字）
    """

    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名",
        examples=["zhangsan"]
    )
    password: str = Field(
        ...,
        min_length=8,
        description="密码（最小8位，必须包含字母和数字）",
        examples=["Password123"]
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        验证用户名格式

        只允许字母、数字、下划线
        """
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        验证密码强度

        必须包含至少一个字母和一个数字
        """
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("密码必须包含至少一个字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class RegisterResponse(BaseModel):
    """
    用户注册响应 DTO

    Attributes:
        user_id: 用户 ID
        name: 用户名
    """

    user_id: str = Field(..., description="用户ID")
    name: str = Field(..., description="用户名")
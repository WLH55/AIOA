"""
用户响应 DTO

定义用户信息查询接口的响应数据结构
"""
from typing import List
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """
    用户信息响应 DTO

    使用 camelCase 与前端保持一致
    """

    id: str = Field(..., description="用户 ID")
    name: str = Field(..., description="用户名")
    status: int = Field(default=0, description="状态(0-正常, 1-禁用)")

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        """
        从 User 模型创建响应 DTO

        Args:
            user: User 实体对象

        Returns:
            UserResponse 实例
        """
        return cls(
            id=str(user.id),
            name=user.name,
            status=user.status,
        )


class UserListResponse(BaseModel):
    """
    用户列表响应 DTO
    """

    count: int = Field(..., description="总数")
    data: List[UserResponse] = Field(default_factory=list, description="用户列表")
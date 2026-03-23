"""
用户响应 DTO

定义用户信息查询接口的响应数据结构
"""
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """
    用户信息响应 DTO

    Attributes:
        user_id: 用户 ID
        name: 用户名
        status: 状态（0-正常，1-禁用）
        is_admin: 是否为管理员
        create_at: 创建时间戳
        update_at: 更新时间戳
    """

    user_id: str = Field(..., description="用户 ID")
    name: str = Field(..., description="用户名")
    status: int = Field(default=0, description="状态(0-正常, 1-禁用)")
    is_admin: bool = Field(default=False, description="是否为管理员")
    create_at: int = Field(..., description="创建时间戳")
    update_at: int = Field(..., description="更新时间戳")

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
            user_id=str(user.id),
            name=user.name,
            status=user.status,
            is_admin=user.isAdmin,
            create_at=user.createAt,
            update_at=user.updateAt,
        )
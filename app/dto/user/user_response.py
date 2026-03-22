"""
用户响应 DTO

定义用户信息查询接口的响应数据结构
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """
    用户信息响应 DTO

    Attributes:
        user_id: 用户 ID
        username: 用户名
        email: 邮箱地址
        full_name: 真实姓名
        department: 部门
        position: 职位
        employee_id: 工号
        phone: 手机号
        avatar_url: 头像 URL
        status: 状态
        roles: 角色列表
        created_at: 创建时间
        updated_at: 更新时间
        last_login_at: 最后登录时间
    """

    user_id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="真实姓名")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="职位")
    employee_id: Optional[str] = Field(None, description="工号")
    phone: Optional[str] = Field(None, description="手机号")
    avatar_url: Optional[str] = Field(None, description="头像 URL")
    status: str = Field(..., description="状态")
    roles: list[str] = Field(default_factory=list, description="角色列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")

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
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            position=user.position,
            employee_id=user.employee_id,
            phone=user.phone,
            avatar_url=user.avatar_url,
            status=user.status,
            roles=user.roles,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )
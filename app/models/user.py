"""
用户实体模型

使用 Beanie ODM 定义 MongoDB Document
"""
from datetime import datetime
from typing import List, Optional
from pydantic import Field, EmailStr
from beanie import Document, Indexed


class User(Document):
    """
    用户文档模型

    Attributes:
        username: 用户名（唯一）
        email: 邮箱（唯一）
        password_hash: 密码哈希值
        full_name: 真实姓名
        department: 部门
        position: 职位
        employee_id: 工号
        phone: 手机号
        avatar_url: 头像 URL
        status: 状态 (active/inactive/suspended)
        roles: 角色列表
        created_at: 创建时间
        updated_at: 更新时间
        last_login_at: 最后登录时间
    """

    # 认证信息
    username: Indexed(str, unique=True) = Field(..., min_length=3, max_length=50, description="用户名")
    email: Indexed(EmailStr, unique=True) = Field(..., description="邮箱")
    password_hash: str = Field(..., description="密码哈希值")

    # 个人信息
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    department: Optional[str] = Field(None, max_length=50, description="部门")
    position: Optional[str] = Field(None, max_length=50, description="职位")
    employee_id: Optional[Indexed(str)] = Field(None, max_length=50, description="工号")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像 URL")

    # 状态与权限
    status: Indexed(str) = Field(default="active", description="状态")
    roles: List[str] = Field(default_factory=lambda: ["user"], description="角色列表")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")

    class Settings:
        """Beanie 设置"""
        name = "users"
        indexes = [
            "username",
            "email",
            "employee_id",
            "status",
        ]

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "username": "zhangsan",
                "email": "zhangsan@company.com",
                "password_hash": "$2b$12$...",
                "full_name": "张三",
                "department": "技术部",
                "position": "后端工程师",
                "employee_id": "E001",
                "phone": "13800138000",
                "status": "active",
                "roles": ["user"],
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updated_at = datetime.utcnow()

    def update_login_time(self) -> None:
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
        self.update_timestamp()
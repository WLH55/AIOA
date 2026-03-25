"""
群组请求 DTO 模块

定义群组相关的请求参数
"""
from typing import List
from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    """
    创建群组请求 DTO
    """

    name: str = Field(..., min_length=1, max_length=50, description="群组名称", alias="groupName")
    avatar: str | None = Field(default=None, description="群头像URL")
    memberIds: List[str] = Field(..., min_length=1, description="初始成员ID列表")

    model_config = {"populate_by_name": True}


class InviteMemberRequest(BaseModel):
    """
    邀请成员请求 DTO
    """

    memberIds: List[str] = Field(..., min_length=1, description="要邀请的成员ID列表")


class RemoveMemberRequest(BaseModel):
    """
    移除成员请求 DTO
    """

    memberId: str = Field(..., description="要移除的成员ID")


class UpdateGroupRequest(BaseModel):
    """
    修改群组信息请求 DTO
    """

    name: str | None = Field(default=None, min_length=1, max_length=50, description="群组名称")
    avatar: str | None = Field(default=None, description="群头像URL")


class GroupListRequest(BaseModel):
    """
    群组列表请求 DTO
    """

    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=20, ge=1, le=100, description="每页数量")

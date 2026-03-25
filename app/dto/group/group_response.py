"""
群组响应 DTO 模块

定义群组相关的响应数据结构
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class GroupMemberResponse(BaseModel):
    """
    群组成员响应 DTO
    """

    userId: str = Field(..., description="用户ID")
    userName: str = Field(..., description="用户名")
    isOwner: bool = Field(default=False, description="是否为群主")


class GroupResponse(BaseModel):
    """
    群组详情响应 DTO
    """

    id: str = Field(..., description="群组ID")
    name: str = Field(..., description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")
    ownerId: str = Field(..., description="群主ID")
    ownerName: str = Field(..., description="群主名称")
    memberIds: List[str] = Field(default_factory=list, description="成员ID列表")
    members: List[GroupMemberResponse] = Field(default_factory=list, description="成员详情列表")
    memberCount: int = Field(..., description="成员数量")
    status: int = Field(..., description="状态")
    createAt: int = Field(..., description="创建时间戳")
    updateAt: int = Field(..., description="更新时间戳")


class GroupListItemResponse(BaseModel):
    """
    群组列表项响应 DTO
    """

    id: str = Field(..., description="群组ID")
    name: str = Field(..., description="群组名称")
    avatar: Optional[str] = Field(None, description="群头像URL")
    ownerId: str = Field(..., description="群主ID")
    ownerName: str = Field(..., description="群主名称")
    memberCount: int = Field(..., description="成员数量")
    status: int = Field(..., description="状态")
    createAt: int = Field(..., description="创建时间戳")


class GroupListResponse(BaseModel):
    """
    群组列表响应 DTO
    """

    count: int = Field(..., description="总数")
    data: List[GroupListItemResponse] = Field(default_factory=list, description="群组列表")

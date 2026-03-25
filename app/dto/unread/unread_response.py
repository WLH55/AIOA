"""
未读消息计数响应 DTO
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class UnreadCountItemResponse(BaseModel):
    """
    未读计数项响应 DTO
    """
    conversationId: str = Field(..., description="会话ID")
    conversationType: int = Field(..., description="会话类型：1=群组，2=私聊")
    unreadCount: int = Field(..., description="未读数量")
    updateAt: int = Field(..., description="更新时间戳")


class UnreadListResponse(BaseModel):
    """
    未读列表响应 DTO
    """
    total: int = Field(..., description="总未读数量")
    list: List[UnreadCountItemResponse] = Field(default_factory=list, description="未读项列表")


class UnreadIncrementResponse(BaseModel):
    """
    未读增量响应 DTO
    """
    userId: str = Field(..., description="用户ID")
    conversationId: str = Field(..., description="会话ID")
    unreadCount: int = Field(..., description="更新后的未读数量")
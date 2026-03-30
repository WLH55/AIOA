"""
AI 会话响应 DTO
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    """AI 会话响应"""
    id: str = Field(..., description="会话ID")
    userId: str = Field(..., description="所属用户ID")
    title: Optional[str] = Field(None, description="会话标题")
    status: int = Field(..., description="状态")
    createdAt: int = Field(..., description="创建时间戳")
    updatedAt: int = Field(..., description="更新时间戳")


class ConversationListResponse(BaseModel):
    """AI 会话列表响应"""
    list: List[ConversationResponse] = Field(default_factory=list, description="会话列表")
    total: int = Field(default=0, description="总数")


class MessageResponse(BaseModel):
    """AI 对话消息响应"""
    id: str = Field(..., description="消息ID")
    sendId: str = Field(..., description="发送者ID")
    msgContent: str = Field(..., description="消息内容")
    sendTime: int = Field(..., description="发送时间戳")


class MessageListResponse(BaseModel):
    """AI 对话消息列表响应"""
    list: List[MessageResponse] = Field(default_factory=list, description="消息列表")
    total: int = Field(default=0, description="总数")

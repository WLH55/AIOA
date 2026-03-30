"""
AI 会话请求 DTO
"""
from typing import Optional
from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    """创建 AI 会话请求"""
    title: Optional[str] = Field(None, max_length=50, description="会话标题")


class DeleteConversationRequest(BaseModel):
    """删除 AI 会话请求"""
    conversationId: str = Field(..., min_length=24, max_length=24, description="会话ID")

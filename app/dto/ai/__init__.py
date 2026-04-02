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


class ChatStreamRequest(BaseModel):
    """AI 对话 SSE 流式请求"""
    conversationId: str = Field(..., min_length=24, max_length=24, description="会话ID")
    content: str = Field(..., min_length=1, max_length=4000, description="用户消息内容")

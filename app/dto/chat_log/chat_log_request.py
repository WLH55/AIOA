"""
聊天记录请求 DTO 模块

定义聊天记录相关的请求参数
"""
from typing import Optional
from pydantic import BaseModel, Field


class ChatLogRequest(BaseModel):
    """
    聊天记录请求 DTO

    用于创建聊天记录
    """

    conversationId: str = Field(..., description="会话ID")
    sendId: str = Field(..., description="发送者用户ID")
    recvId: Optional[str] = Field(None, description="接收者用户ID(群聊时为空)")
    chatType: int = Field(default=1, description="聊天类型(1-群聊, 2-私聊)")
    msgContent: str = Field(..., description="消息内容")


class ChatLogListRequest(BaseModel):
    """
    聊天记录列表请求 DTO
    """

    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=20, ge=1, le=100, description="每页数量")
    conversationId: Optional[str] = Field(None, description="会话ID")
    sendId: Optional[str] = Field(None, description="发送者用户ID")
    chatType: Optional[int] = Field(None, description="聊天类型")
    startTime: Optional[int] = Field(None, description="开始时间戳(毫秒)")
    endTime: Optional[int] = Field(None, description="结束时间戳(毫秒)")
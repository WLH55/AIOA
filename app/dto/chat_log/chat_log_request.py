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

    conversation_id: str = Field(..., description="会话ID")
    send_id: str = Field(..., description="发送者用户ID")
    recv_id: Optional[str] = Field(None, description="接收者用户ID(群聊时为空)")
    chat_type: int = Field(default=1, description="聊天类型(1-群聊, 2-私聊)")
    msg_content: str = Field(..., description="消息内容")


class ChatLogListRequest(BaseModel):
    """
    聊天记录列表请求 DTO
    """

    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=20, ge=1, le=100, description="每页数量")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    send_id: Optional[str] = Field(None, description="发送者用户ID")
    chat_type: Optional[int] = Field(None, description="聊天类型")
    start_time: Optional[int] = Field(None, description="开始时间戳(毫秒)")
    end_time: Optional[int] = Field(None, description="结束时间戳(毫秒)")
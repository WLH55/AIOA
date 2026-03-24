"""
聊天记录响应 DTO 模块

定义聊天记录相关的响应数据结构
"""
from typing import Optional
from pydantic import BaseModel, Field


class ChatLogResponse(BaseModel):
    """
    聊天记录响应 DTO
    """

    id: str = Field(..., description="记录ID")
    conversation_id: str = Field(..., description="会话ID")
    send_id: str = Field(..., description="发送者用户ID")
    send_name: Optional[str] = Field(None, description="发送者用户名")
    recv_id: Optional[str] = Field(None, description="接收者用户ID")
    recv_name: Optional[str] = Field(None, description="接收者用户名")
    chat_type: int = Field(default=1, description="聊天类型(1-群聊, 2-私聊)")
    msg_content: str = Field(..., description="消息内容")
    send_time: Optional[int] = Field(None, description="发送时间戳")
    create_at: Optional[int] = Field(None, description="创建时间戳")


class ChatLogListResponse(BaseModel):
    """
    聊天记录列表响应 DTO
    """

    count: int = Field(..., description="总数")
    data: list[ChatLogResponse] = Field(default_factory=list, description="聊天记录列表")
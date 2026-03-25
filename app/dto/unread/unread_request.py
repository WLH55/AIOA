"""
未读消息计数请求 DTO
"""
from pydantic import BaseModel, Field


class GetUnreadListRequest(BaseModel):
    """
    获取未读列表请求 DTO
    """
    conversationType: int = Field(None, description="会话类型：1=群组，2=私聊")


class ClearUnreadRequest(BaseModel):
    """
    清除未读计数请求 DTO
    """
    conversationId: str = Field(..., description="会话ID")
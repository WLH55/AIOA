"""
WebSocket AI 消息 DTO

定义 AI 对话相关的 WebSocket 消息数据结构
"""
from typing import Optional
from pydantic import BaseModel, Field


class AiChatMessage(BaseModel):
    """
    用户发送的 AI 对话消息

    客户端通过 WebSocket 发送给服务端
    """
    type: str = Field(default="ai_chat", description="消息类型")
    conversationId: str = Field(..., description="会话ID")
    content: str = Field(..., min_length=1, description="用户消息内容")


class AiChunkMessage(BaseModel):
    """
    AI 流式响应片段

    服务端推送给客户端的流式文本片段
    """
    type: str = Field(default="ai_chunk", description="消息类型")
    conversationId: str = Field(..., description="会话ID")
    content: str = Field(..., description="本片段文本")
    index: int = Field(..., description="片段序号")


class AiCompleteMessage(BaseModel):
    """
    AI 响应完成消息

    包含 AI 的完整响应内容
    """
    type: str = Field(default="ai_complete", description="消息类型")
    conversationId: str = Field(..., description="会话ID")
    content: str = Field(..., description="完整响应内容")
    messageId: str = Field(..., description="AI 响应消息的 ChatLog ID")


class AiToolCallMessage(BaseModel):
    """
    工具调用通知

    通知客户端 AI 正在调用某个工具
    """
    type: str = Field(default="ai_tool_call", description="消息类型")
    conversationId: str = Field(..., description="会话ID")
    tool: str = Field(..., description="工具名称")
    args: dict = Field(default_factory=dict, description="调用参数")
    status: str = Field(default="running", description="执行状态")


class AiToolResultMessage(BaseModel):
    """
    工具执行结果

    通知客户端工具的执行结果
    """
    type: str = Field(default="ai_tool_result", description="消息类型")
    conversationId: str = Field(..., description="会话ID")
    tool: str = Field(..., description="工具名称")
    result: str = Field(..., description="执行结果")
    status: str = Field(..., description="success 或 error")


class AiErrorMessage(BaseModel):
    """
    AI 处理错误消息

    通知客户端 AI 处理过程中出现的错误
    """
    type: str = Field(default="ai_error", description="消息类型")
    conversationId: str = Field(..., description="会话ID")
    error: str = Field(..., description="错误码")
    message: str = Field(..., description="错误描述")

"""
DeepSeek LLM 客户端封装

基于 LangChain ChatOpenAI 配置 DeepSeek API 连接，支持流式输出和工具绑定
"""
import logging

from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def get_chat_llm(streaming: bool = True) -> ChatOpenAI:
    """
    获取 ChatOpenAI 实例（DeepSeek API）

    Args:
        streaming: 是否启用流式输出

    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        model=settings.DEEPSEEK_MODEL,
        streaming=streaming,
        temperature=0.7,
        max_tokens=4096,
        timeout=settings.AI_TIMEOUT,
    )


def get_summary_llm() -> ChatOpenAI:
    """
    获取用于摘要生成的 LLM 实例

    不启用流式输出，摘要生成使用同步调用

    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        model=settings.AI_SUMMARY_MODEL,
        streaming=False,
        temperature=0.3,
        max_tokens=1024,
        timeout=settings.AI_TIMEOUT,
    )

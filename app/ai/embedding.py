"""
SiliconFlow Embedding 客户端

基于 LangChain OpenAIEmbeddings 封装 SiliconFlow BAAI/bge-m3 模型，
通过 OpenAI 兼容接口接入，支持单条和批量文本向量化。
"""
import logging
from typing import List, Optional

from langchain_openai import OpenAIEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

# 单次批量 embedding 最大条数（SiliconFlow 限制）
_BATCH_SIZE = 32


def get_embedding_client() -> OpenAIEmbeddings:
    """
    获取 SiliconFlow Embedding 客户端实例

    使用 OpenAI 兼容接口连接 SiliconFlow API

    Returns:
        OpenAIEmbeddings 实例

    Raises:
        ValueError: API Key 未配置时抛出
    """
    if not settings.SILICONFLOW_API_KEY:
        raise ValueError("SILICONFLOW_API_KEY 未配置，知识库功能不可用")
    return OpenAIEmbeddings(
        api_key=settings.SILICONFLOW_API_KEY,
        base_url=settings.SILICONFLOW_BASE_URL,
        model=settings.SILICONFLOW_EMBEDDING_MODEL,
        dimensions=settings.SILICONFLOW_EMBEDDING_DIMENSIONS,
        check_embedding_ctx_length=False,
    )


async def embed_text(text: str) -> List[float]:
    """
    将单条文本转换为向量

    Args:
        text: 输入文本

    Returns:
        浮点数列表（向量）
    """
    client = get_embedding_client()
    return await client.aembed_query(text)


async def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    批量文本向量化

    自动按 _BATCH_SIZE 分批调用，避免 API 限制

    Args:
        texts: 文本列表

    Returns:
        向量列表
    """
    client = get_embedding_client()
    if len(texts) <= _BATCH_SIZE:
        return await client.aembed_documents(texts)
    # 分批处理
    results: List[List[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i:i + _BATCH_SIZE]
        batch_embeddings = await client.aembed_documents(batch)
        results.extend(batch_embeddings)
        logger.debug(f"Embedding 批次 {i // _BATCH_SIZE + 1}: {len(batch)} 条")
    return results

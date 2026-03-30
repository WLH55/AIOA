"""
摘要缓冲实现

管理 Redis 中的对话缓冲，提供 Token 估算和摘要触发判断
"""
import json
import logging
from typing import List, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

# Redis Key 前缀
_BUFFER_PREFIX = "ai:buffer:"
_SUMMARY_PREFIX = "ai:summary:"


class SummaryBuffer:
    """
    摘要缓冲管理器

    管理 Redis 中的对话缓冲区，提供：
    - 对话缓冲的读写
    - Token 估算（tokenCount = charCount * 1.5）
    - 摘要触发判断
    """

    def __init__(self, redis_client):
        """
        初始化摘要缓冲管理器

        Args:
            redis_client: Redis 异步客户端
        """
        self._redis = redis_client
        self._max_token_limit = settings.AI_MEMORY_MAX_TOKEN_LIMIT
        self._redis_ttl = settings.AI_MEMORY_REDIS_TTL

    def _buffer_key(self, conversation_id: str) -> str:
        """获取对话缓冲的 Redis Key"""
        return f"{_BUFFER_PREFIX}{conversation_id}"

    def _summary_key(self, conversation_id: str) -> str:
        """获取摘要缓存的 Redis Key"""
        return f"{_SUMMARY_PREFIX}{conversation_id}"

    @staticmethod
    def estimate_token_count(char_count: int) -> int:
        """
        估算 Token 数量

        Args:
            char_count: 字符数

        Returns:
            估算的 Token 数量
        """
        return int(char_count * 1.5)

    async def add_message(self, conversation_id: str, role: str, content: str) -> int:
        """
        添加一条消息到缓冲区

        Args:
            conversation_id: 会话 ID
            role: 消息角色（user/assistant）
            content: 消息内容

        Returns:
            添加后的缓冲区总字符数
        """
        key = self._buffer_key(conversation_id)
        message = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        await self._redis.rpush(key, message)
        await self._redis.expire(key, self._redis_ttl)
        # 返回缓冲区总字符数
        return await self.get_char_count(conversation_id)

    async def get_char_count(self, conversation_id: str) -> int:
        """
        获取缓冲区的总字符数

        Args:
            conversation_id: 会话 ID

        Returns:
            总字符数
        """
        key = self._buffer_key(conversation_id)
        messages = await self._redis.lrange(key, 0, -1)
        total = sum(len(msg) for msg in messages)
        return total

    def should_trigger_summary(self, char_count: int) -> bool:
        """
        判断是否需要触发摘要压缩

        Args:
            char_count: 当前缓冲区字符数

        Returns:
            是否需要触发摘要
        """
        return char_count > self._max_token_limit

    async def get_buffer_messages(self, conversation_id: str) -> List[dict]:
        """
        获取缓冲区中的所有消息

        Args:
            conversation_id: 会话 ID

        Returns:
            消息列表
        """
        key = self._buffer_key(conversation_id)
        raw_messages = await self._redis.lrange(key, 0, -1)
        messages = []
        for raw in raw_messages:
            try:
                messages.append(json.loads(raw))
            except json.JSONDecodeError:
                logger.warning(f"解析缓冲消息失败: {raw[:100]}")
        return messages

    async def clear_buffer(self, conversation_id: str) -> None:
        """
        清空缓冲区

        Args:
            conversation_id: 会话 ID
        """
        key = self._buffer_key(conversation_id)
        await self._redis.delete(key)

    async def keep_recent_messages(self, conversation_id: str, count: int = 10) -> None:
        """
        降级策略：只保留最近 N 条消息

        Args:
            conversation_id: 会话 ID
            count: 保留的消息数
        """
        key = self._buffer_key(conversation_id)
        # 保留最后 count 条消息
        total = await self._redis.llen(key)
        if total > count:
            # 删除前面的消息，保留最后 count 条
            await self._redis.ltrim(key, total - count, -1)
            logger.info(f"降级策略：保留最近 {count} 条消息, conversationId={conversation_id}")

    async def get_summary(self, conversation_id: str) -> Optional[str]:
        """
        获取 Redis 中缓存的摘要

        Args:
            conversation_id: 会话 ID

        Returns:
            摘要文本或 None
        """
        key = self._summary_key(conversation_id)
        summary = await self._redis.get(key)
        if summary:
            return summary.decode("utf-8") if isinstance(summary, bytes) else summary
        return None

    async def set_summary(self, conversation_id: str, summary: str) -> None:
        """
        设置摘要到 Redis 缓存

        Args:
            conversation_id: 会话 ID
            summary: 摘要文本
        """
        key = self._summary_key(conversation_id)
        await self._redis.set(key, summary, ex=self._redis_ttl)

    async def clear_all(self, conversation_id: str) -> None:
        """
        清除会话的所有 Redis 缓存（缓冲和摘要）

        Args:
            conversation_id: 会话 ID
        """
        await self._redis.delete(self._buffer_key(conversation_id))
        await self._redis.delete(self._summary_key(conversation_id))

"""
摘要缓冲实现

管理 Redis 中的对话缓冲，提供动态阈值计算和摘要触发判断
基于模型上下文窗口自动计算压缩阈值，借鉴 Claude Code 的设计
"""
import json
import logging
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# Redis Key 前缀
_BUFFER_PREFIX = "ai:buffer:"
_SUMMARY_PREFIX = "ai:summary:"
_FAILURE_PREFIX = "ai:failure:"


class SummaryBuffer:
    """
    摘要缓冲管理器

    管理 Redis 中的对话缓冲区，提供：
    - 动态阈值计算（基于模型上下文窗口）
    - 对话缓冲的读写
    - 字符数估算（中文字符与 token 约为 1:1.5 关系）
    - 摘要触发判断
    - 熔断器机制
    """

    def __init__(self, redis_client):
        """
        初始化摘要缓冲管理器

        Args:
            redis_client: Redis 异步客户端
        """
        self._redis = redis_client
        self._redis_ttl = settings.AI_MEMORY_REDIS_TTL
        # 动态计算阈值
        self._context_window = settings.AI_MODEL_CONTEXT_WINDOW
        self._reserved_tokens = settings.AI_MEMORY_RESERVED_TOKENS
        self._buffer_tokens = settings.AI_MEMORY_BUFFER_TOKENS
        self._max_failures = settings.AI_MEMORY_MAX_FAILURES
        self._keep_recent_count = settings.AI_MEMORY_KEEP_RECENT_COUNT

    def _buffer_key(self, conversation_id: str) -> str:
        """获取对话缓冲的 Redis Key"""
        return f"{_BUFFER_PREFIX}{conversation_id}"

    def _summary_key(self, conversation_id: str) -> str:
        """获取摘要缓存的 Redis Key"""
        return f"{_SUMMARY_PREFIX}{conversation_id}"

    def _failure_key(self, conversation_id: str) -> str:
        """获取熔断器计数的 Redis Key"""
        return f"{_FAILURE_PREFIX}{conversation_id}"

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

    @staticmethod
    def estimate_char_count(token_count: int) -> int:
        """
        估算字符数量

        Args:
            token_count: Token 数量

        Returns:
            估算的字符数
        """
        return int(token_count / 1.5)

    def get_auto_compact_threshold(self) -> int:
        """
        获取自动压缩触发阈值（字符数）

        计算：context_window - reserved_tokens - buffer_tokens
        即：128K - 20K - 13K = 95K tokens ≈ 63,333 字符

        Returns:
            自动压缩触发的字符数阈值
        """
        threshold_tokens = self._context_window - self._reserved_tokens - self._buffer_tokens
        threshold_chars = self.estimate_char_count(threshold_tokens)
        logger.debug(
            f"自动压缩阈值: {threshold_chars} 字符 "
            f"(tokens={threshold_tokens}, 窗口={self._context_window})"
        )
        return threshold_chars

    def get_effective_context_window(self) -> int:
        """
        获取有效上下文窗口（tokens）

        计算：context_window - reserved_tokens
        即：128K - 20K = 108K tokens

        Returns:
            有效上下文窗口（tokens）
        """
        return self._context_window - self._reserved_tokens

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
        threshold = self.get_auto_compact_threshold()
        return char_count > threshold

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

    async def keep_recent_messages(self, conversation_id: str, count: int = None) -> None:
        """
        降级策略：只保留最近 N 条消息

        Args:
            conversation_id: 会话 ID
            count: 保留的消息数，默认使用配置值
        """
        if count is None:
            count = self._keep_recent_count
        key = self._buffer_key(conversation_id)
        total = await self._redis.llen(key)
        if total > count:
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

    async def get_failure_count(self, conversation_id: str) -> int:
        """
        获取熔断器失败计数

        Args:
            conversation_id: 会话 ID

        Returns:
            连续失败次数
        """
        key = self._failure_key(conversation_id)
        count = await self._redis.get(key)
        if count:
            return int(count.decode("utf-8") if isinstance(count, bytes) else count)
        return 0

    async def increment_failure_count(self, conversation_id: str) -> int:
        """
        增加熔断器失败计数

        Args:
            conversation_id: 会话 ID

        Returns:
            增加后的失败次数
        """
        key = self._failure_key(conversation_id)
        count = await self._redis.incr(key)
        await self._redis.expire(key, self._redis_ttl)
        return count

    async def reset_failure_count(self, conversation_id: str) -> None:
        """
        重置熔断器失败计数

        Args:
            conversation_id: 会话 ID
        """
        key = self._failure_key(conversation_id)
        await self._redis.delete(key)

    def is_circuit_breaker_open(self, failure_count: int) -> bool:
        """
        判断熔断器是否开启

        Args:
            failure_count: 连续失败次数

        Returns:
            是否熔断
        """
        return failure_count >= self._max_failures

    async def clear_all(self, conversation_id: str) -> None:
        """
        清除会话的所有 Redis 缓存（缓冲、摘要、熔断计数）

        Args:
            conversation_id: 会话 ID
        """
        await self._redis.delete(self._buffer_key(conversation_id))
        await self._redis.delete(self._summary_key(conversation_id))
        await self._redis.delete(self._failure_key(conversation_id))
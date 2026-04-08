"""
AI 记忆管理单元测试

覆盖 Token 估算、动态阈值计算、摘要触发、熔断器、摘要生成、记忆获取
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.memory.summary_buffer import SummaryBuffer
from app.ai.memory.memory_manager import MemoryManager


# ==================== Token 估算测试 ====================


class TestTokenEstimation:
    """TC-2.1 Token 估算测试"""

    def test_estimate_token_chinese_text(self):
        """TC-2.1.1: 正常中文文本 1000 字符 -> 1500 token"""
        result = SummaryBuffer.estimate_token_count(1000)
        assert result == 1500

    def test_estimate_token_empty_text(self):
        """TC-2.1.2: 空文本 0 字符 -> 0 token"""
        result = SummaryBuffer.estimate_token_count(0)
        assert result == 0

    def test_estimate_token_mixed_text(self):
        """TC-2.1.3: 混合文本 500 字符 -> 750 token"""
        result = SummaryBuffer.estimate_token_count(500)
        assert result == 750

    def test_estimate_char_from_token(self):
        """TC-2.1.4: Token 转字符 1500 token -> 1000 字符"""
        result = SummaryBuffer.estimate_char_count(1500)
        assert result == 1000


# ==================== 动态阈值计算测试 ====================


class TestDynamicThreshold:
    """动态阈值计算测试"""

    def _make_buffer(self):
        """创建测试用 SummaryBuffer"""
        mock_redis = AsyncMock()
        with patch("app.ai.memory.summary_buffer.settings") as mock_settings:
            mock_settings.AI_MODEL_CONTEXT_WINDOW = 128000
            mock_settings.AI_MEMORY_RESERVED_TOKENS = 20000
            mock_settings.AI_MEMORY_BUFFER_TOKENS = 13000
            mock_settings.AI_MEMORY_MAX_FAILURES = 3
            mock_settings.AI_MEMORY_KEEP_RECENT_COUNT = 10
            mock_settings.AI_MEMORY_REDIS_TTL = 86400
            buffer = SummaryBuffer(mock_redis)
        return buffer

    def test_auto_compact_threshold(self):
        """动态阈值计算：128K - 20K - 13K = 95K tokens ≈ 63,333 字符"""
        buffer = self._make_buffer()
        threshold = buffer.get_auto_compact_threshold()
        # 95K tokens / 1.5 ≈ 63,333 字符
        assert threshold == 63333

    def test_effective_context_window(self):
        """有效上下文窗口：128K - 20K = 108K tokens"""
        buffer = self._make_buffer()
        window = buffer.get_effective_context_window()
        assert window == 108000

    def test_should_not_trigger_under_threshold(self):
        """低于阈值不触发压缩"""
        buffer = self._make_buffer()
        assert buffer.should_trigger_summary(50000) is False

    def test_should_trigger_over_threshold(self):
        """超过阈值触发压缩"""
        buffer = self._make_buffer()
        assert buffer.should_trigger_summary(70000) is True


# ==================== 熔断器测试 ====================


class TestCircuitBreaker:
    """熔断器机制测试"""

    def _make_buffer(self):
        """创建测试用 SummaryBuffer"""
        mock_redis = AsyncMock()
        with patch("app.ai.memory.summary_buffer.settings") as mock_settings:
            mock_settings.AI_MODEL_CONTEXT_WINDOW = 128000
            mock_settings.AI_MEMORY_RESERVED_TOKENS = 20000
            mock_settings.AI_MEMORY_BUFFER_TOKENS = 13000
            mock_settings.AI_MEMORY_MAX_FAILURES = 3
            mock_settings.AI_MEMORY_KEEP_RECENT_COUNT = 10
            mock_settings.AI_MEMORY_REDIS_TTL = 86400
            buffer = SummaryBuffer(mock_redis)
        return buffer

    def test_circuit_breaker_closed_under_threshold(self):
        """失败次数 < 3，熔断器关闭"""
        buffer = self._make_buffer()
        assert buffer.is_circuit_breaker_open(2) is False

    def test_circuit_breaker_open_at_threshold(self):
        """失败次数 >= 3，熔断器开启"""
        buffer = self._make_buffer()
        assert buffer.is_circuit_breaker_open(3) is True
        assert buffer.is_circuit_breaker_open(4) is True

    @pytest.mark.asyncio
    async def test_get_failure_count_zero(self):
        """初始失败计数为 0"""
        buffer = self._make_buffer()
        buffer._redis.get = AsyncMock(return_value=None)

        count = await buffer.get_failure_count("conv1")

        assert count == 0

    @pytest.mark.asyncio
    async def test_increment_failure_count(self):
        """增加失败计数"""
        buffer = self._make_buffer()
        buffer._redis.incr = AsyncMock(return_value=1)
        buffer._redis.expire = AsyncMock()

        count = await buffer.increment_failure_count("conv1")

        assert count == 1

    @pytest.mark.asyncio
    async def test_reset_failure_count(self):
        """重置失败计数"""
        buffer = self._make_buffer()

        await buffer.reset_failure_count("conv1")

        buffer._redis.delete.assert_called_once()


# ==================== 摘要缓冲操作测试 ====================


class TestSummaryBuffer:
    """摘要缓冲 Redis 操作测试"""

    def _make_buffer(self):
        """创建测试用 SummaryBuffer"""
        mock_redis = AsyncMock()
        with patch("app.ai.memory.summary_buffer.settings") as mock_settings:
            mock_settings.AI_MODEL_CONTEXT_WINDOW = 128000
            mock_settings.AI_MEMORY_RESERVED_TOKENS = 20000
            mock_settings.AI_MEMORY_BUFFER_TOKENS = 13000
            mock_settings.AI_MEMORY_MAX_FAILURES = 3
            mock_settings.AI_MEMORY_KEEP_RECENT_COUNT = 10
            mock_settings.AI_MEMORY_REDIS_TTL = 86400
            buffer = SummaryBuffer(mock_redis)
        return buffer

    @pytest.mark.asyncio
    async def test_add_message(self):
        """添加消息到缓冲区"""
        buffer = self._make_buffer()
        buffer._redis.lrange = AsyncMock(return_value=[])

        char_count = await buffer.add_message("conv1", "user", "你好")

        buffer._redis.rpush.assert_called_once()
        buffer._redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_buffer_messages(self):
        """获取缓冲区消息"""
        buffer = self._make_buffer()
        msg = json.dumps({"role": "user", "content": "你好"}, ensure_ascii=False)
        buffer._redis.lrange = AsyncMock(return_value=[msg.encode("utf-8")])

        messages = await buffer.get_buffer_messages("conv1")

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "你好"

    @pytest.mark.asyncio
    async def test_clear_buffer(self):
        """清空缓冲区"""
        buffer = self._make_buffer()

        await buffer.clear_buffer("conv1")

        buffer._redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_keep_recent_messages_under_limit(self):
        """降级策略：消息数不超过限制时不裁剪"""
        buffer = self._make_buffer()
        buffer._redis.llen = AsyncMock(return_value=5)

        await buffer.keep_recent_messages("conv1", 10)

        buffer._redis.ltrim.assert_not_called()

    @pytest.mark.asyncio
    async def test_keep_recent_messages_over_limit(self):
        """降级策略：消息数超过限制时裁剪到最近 N 条"""
        buffer = self._make_buffer()
        buffer._redis.llen = AsyncMock(return_value=20)

        await buffer.keep_recent_messages("conv1", 10)

        buffer._redis.ltrim.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_summary_hit(self):
        """Redis 缓存命中"""
        buffer = self._make_buffer()
        buffer._redis.get = AsyncMock(return_value="这是一个摘要".encode("utf-8"))

        result = await buffer.get_summary("conv1")

        assert result == "这是一个摘要"

    @pytest.mark.asyncio
    async def test_get_summary_miss(self):
        """Redis 缓存未命中"""
        buffer = self._make_buffer()
        buffer._redis.get = AsyncMock(return_value=None)

        result = await buffer.get_summary("conv1")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_summary(self):
        """设置摘要到 Redis"""
        buffer = self._make_buffer()

        await buffer.set_summary("conv1", "新摘要")

        buffer._redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_char_count(self):
        """获取缓冲区字符数"""
        buffer = self._make_buffer()
        msgs = [
            json.dumps({"role": "user", "content": "你好世界"}).encode("utf-8"),
            json.dumps({"role": "assistant", "content": "你好"}).encode("utf-8"),
        ]
        buffer._redis.lrange = AsyncMock(return_value=msgs)

        char_count = await buffer.get_char_count("conv1")

        assert char_count > 0

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """清除所有 Redis 缓存（缓冲、摘要、熔断计数）"""
        buffer = self._make_buffer()

        await buffer.clear_all("conv1")

        # 现在清除 3 个 key（缓冲、摘要、熔断计数）
        assert buffer._redis.delete.call_count == 3


# ==================== 记忆管理器测试 ====================


class TestMemoryManager:
    """记忆管理器测试"""

    def _make_manager(self):
        """创建测试用 MemoryManager"""
        mock_redis = AsyncMock()
        manager = MemoryManager(mock_redis)
        return manager

    @pytest.mark.asyncio
    async def test_get_memory_empty_conversation(self):
        """全新会话返回空记忆"""
        manager = self._make_manager()

        with patch.object(manager, "_get_summary", return_value=None), \
             patch.object(manager._buffer, "get_buffer_messages", return_value=[]), \
             patch.object(manager, "_load_from_mongodb", return_value=[]):
            messages = await manager.get_memory_messages("new_conv")

            assert messages == []

    @pytest.mark.asyncio
    async def test_get_memory_with_summary(self):
        """Redis 有摘要和缓冲"""
        manager = self._make_manager()

        with patch.object(manager, "_get_summary", return_value="之前的对话摘要"), \
             patch.object(manager._buffer, "get_buffer_messages", return_value=[
                 {"role": "user", "content": "你好"},
                 {"role": "assistant", "content": "你好！"},
             ]):
            messages = await manager.get_memory_messages("conv1")

            assert len(messages) == 3
            assert messages[0]["role"] == "system"
            assert "对话摘要" in messages[0]["content"]
            assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_memory_redis_miss_fallback_mongodb(self):
        """Redis 未命中从 MongoDB 兜底加载"""
        manager = self._make_manager()

        with patch.object(manager, "_get_summary", return_value=None), \
             patch.object(manager._buffer, "get_buffer_messages", return_value=[]), \
             patch.object(manager, "_load_from_mongodb", return_value=[
                 {"role": "user", "content": "历史消息"},
             ]), \
             patch.object(manager._buffer, "add_message", return_value=0):
            messages = await manager.get_memory_messages("conv1")

            assert len(messages) == 1
            assert messages[0]["content"] == "历史消息"

    @pytest.mark.asyncio
    async def test_add_user_message(self):
        """添加用户消息到缓冲"""
        manager = self._make_manager()

        with patch.object(manager._buffer, "add_message", return_value=100):
            await manager.add_user_message("conv1", "你好")

            manager._buffer.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_assistant_message_no_summary(self):
        """首次添加 AI 消息（未触发摘要）"""
        manager = self._make_manager()

        with patch.object(manager._buffer, "add_message", return_value=50000), \
             patch.object(manager._buffer, "should_trigger_summary", return_value=False):
            await manager.add_assistant_message("conv1", "这是 AI 的回答")

            manager._buffer.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_assistant_message_trigger_summary(self):
        """添加 AI 消息触发摘要"""
        manager = self._make_manager()

        with patch.object(manager._buffer, "add_message", return_value=70000), \
             patch.object(manager._buffer, "should_trigger_summary", return_value=True), \
             patch.object(manager, "_trigger_summary", return_value=None):
            await manager.add_assistant_message("conv1", "AI 回答")

            manager._trigger_summary.assert_called_once_with("conv1")

    @pytest.mark.asyncio
    async def test_trigger_summary_success(self):
        """摘要成功后缓冲清空"""
        manager = self._make_manager()

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "新的对话摘要"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch.object(manager._buffer, "get_failure_count", return_value=0), \
             patch.object(manager._buffer, "is_circuit_breaker_open", return_value=False), \
             patch.object(manager, "_get_summary", return_value=None), \
             patch.object(manager._buffer, "get_buffer_messages", return_value=[
                 {"role": "user", "content": "你好"},
                 {"role": "assistant", "content": "你好！"},
             ]), \
             patch("app.ai.memory.memory_manager.get_summary_llm", return_value=mock_llm), \
             patch("app.ai.memory.memory_manager.AiSummaryRepository") as mock_summary_repo, \
             patch.object(manager._buffer, "set_summary", return_value=None), \
             patch.object(manager._buffer, "clear_buffer", return_value=None), \
             patch.object(manager._buffer, "reset_failure_count", return_value=None):
            mock_summary_repo.upsert = AsyncMock()

            await manager._trigger_summary("conv1")

            mock_summary_repo.upsert.assert_called_once()
            manager._buffer.set_summary.assert_called_once()
            manager._buffer.clear_buffer.assert_called_once()
            manager._buffer.reset_failure_count.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_summary_failure_increment_count(self):
        """摘要失败增加熔断计数"""
        manager = self._make_manager()

        with patch.object(manager._buffer, "get_failure_count", return_value=0), \
             patch.object(manager._buffer, "is_circuit_breaker_open", return_value=False), \
             patch.object(manager, "_get_summary", side_effect=Exception("LLM Error")), \
             patch.object(manager._buffer, "increment_failure_count", return_value=1), \
             patch.object(manager._buffer, "keep_recent_messages", return_value=None):
            await manager._trigger_summary("conv1")

            manager._buffer.increment_failure_count.assert_called_once()
            manager._buffer.keep_recent_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_summary_circuit_breaker_open(self):
        """熔断器开启时跳过压缩"""
        manager = self._make_manager()

        with patch.object(manager._buffer, "get_failure_count", return_value=3), \
             patch.object(manager._buffer, "is_circuit_breaker_open", return_value=True), \
             patch.object(manager._buffer, "keep_recent_messages", return_value=None):
            await manager._trigger_summary("conv1")

            # 熔断器开启，直接降级，不调用 LLM
            manager._buffer.keep_recent_messages.assert_called_once()
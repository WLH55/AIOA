"""
AI 对话 SSE 流式服务单元测试

覆盖 SSE 事件格式化、SSE generator 流式输出、WS 桥接模式
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_chat_service import AiChatService, _sse_event


# ==================== SSE 事件格式化测试 ====================


class TestSSEEventFormat:
    """SSE 事件格式化测试"""

    def test_sse_event_ai_chunk(self):
        """格式化 ai_chunk 事件"""
        result = _sse_event("ai_chunk", {
            "conversationId": "conv1",
            "content": "你好",
            "index": 1,
        })
        assert "event: ai_chunk\n" in result
        assert "data: " in result
        assert result.endswith("\n\n")
        # 解析 data 部分
        data_line = [l for l in result.strip().split("\n") if l.startswith("data: ")][0]
        data = json.loads(data_line[6:])
        assert data["content"] == "你好"
        assert data["index"] == 1

    def test_sse_event_ai_error(self):
        """格式化 ai_error 事件"""
        result = _sse_event("ai_error", {
            "conversationId": "conv1",
            "error": "AI_SERVICE_ERROR",
            "message": "服务不可用",
        })
        assert "event: ai_error\n" in result
        data_line = [l for l in result.strip().split("\n") if l.startswith("data: ")][0]
        data = json.loads(data_line[6:])
        assert data["error"] == "AI_SERVICE_ERROR"
        assert data["message"] == "服务不可用"

    def test_sse_event_ai_complete(self):
        """格式化 ai_complete 事件"""
        result = _sse_event("ai_complete", {
            "conversationId": "conv1",
            "content": "完整回答",
            "messageId": "msg_123",
        })
        assert "event: ai_complete\n" in result
        data_line = [l for l in result.strip().split("\n") if l.startswith("data: ")][0]
        data = json.loads(data_line[6:])
        assert data["content"] == "完整回答"
        assert data["messageId"] == "msg_123"

    def test_sse_event_tool_call(self):
        """格式化 ai_tool_call 事件"""
        result = _sse_event("ai_tool_call", {
            "conversationId": "conv1",
            "tool": "parseTime",
            "args": {"expression": "明天"},
            "status": "running",
        })
        assert "event: ai_tool_call\n" in result

    def test_sse_event_chinese_content(self):
        """SSE 事件正确处理中文（ensure_ascii=False）"""
        result = _sse_event("ai_chunk", {
            "conversationId": "conv1",
            "content": "你好世界",
            "index": 1,
        })
        # ensure_ascii=False 时中文不会被转义
        assert "你好世界" in result

    def test_sse_event_ends_with_double_newline(self):
        """SSE 事件必须以双换行结尾"""
        result = _sse_event("ai_chunk", {"content": "test", "index": 1})
        assert result.endswith("\n\n")


# ==================== SSE Generator 流式测试 ====================


class TestSSEGenerator:
    """SSE generator 流式输出测试"""

    def _make_user(self, user_id="user1", name="测试用户"):
        """创建 mock 用户"""
        user = MagicMock()
        user.id = user_id
        user.name = name
        return user

    @pytest.mark.asyncio
    async def test_conversation_not_found(self):
        """会话不存在时直接 yield error 事件"""
        user = self._make_user()
        with patch("app.services.ai_chat_service.AiConversationRepository") as mock_repo, \
             patch("app.services.ai_chat_service.ChatLogRepository"):
            mock_repo.find_active_by_id = AsyncMock(return_value=None)
            events = []
            async for event in AiChatService.handle_ai_chat_sse(
                user, "conv_notexist", "你好", None,
            ):
                events.append(event)
            assert len(events) == 1
            assert "event: ai_error" in events[0]
            assert "CONVERSATION_NOT_FOUND" in events[0]

    @pytest.mark.asyncio
    async def test_conversation_forbidden(self):
        """无权访问会话时 yield error 事件"""
        user = self._make_user(user_id="user_a")
        mock_conv = MagicMock()
        mock_conv.userId = "user_b"  # 不同用户
        with patch("app.services.ai_chat_service.AiConversationRepository") as mock_repo, \
             patch("app.services.ai_chat_service.ChatLogRepository"):
            mock_repo.find_active_by_id = AsyncMock(return_value=mock_conv)
            events = []
            async for event in AiChatService.handle_ai_chat_sse(
                user, "conv1", "你好", None,
            ):
                events.append(event)
            assert len(events) == 1
            assert "event: ai_error" in events[0]
            assert "FORBIDDEN" in events[0]

    @pytest.mark.asyncio
    async def test_sse_stream_ai_response(self):
        """正常 SSE 流式响应：接收 ai_chunk + ai_complete 事件"""
        user = self._make_user()
        mock_conv = MagicMock()
        mock_conv.userId = "user1"
        mock_conv.title = "测试"

        mock_response = MagicMock()
        mock_response.content = "这是AI的回答"
        mock_response.tool_calls = None

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        mock_saved_msg = MagicMock()
        mock_saved_msg.id = "msg_saved_123"

        with patch("app.services.ai_chat_service.AiConversationRepository") as mock_conv_repo, \
             patch("app.services.ai_chat_service.ChatLogRepository") as mock_log_repo, \
             patch("app.services.ai_chat_service.ChatLog") as mock_chat_log_cls, \
             patch("app.services.ai_chat_service.MemoryManager") as mock_memory_cls, \
             patch("app.services.ai_chat_service.get_all_tools", return_value=[]), \
             patch("app.services.ai_chat_service.build_system_prompt", return_value="测试提示词"), \
             patch("app.services.ai_chat_service.get_chat_llm", return_value=mock_llm):
            # 配置 mock
            mock_conv_repo.find_active_by_id = AsyncMock(return_value=mock_conv)
            mock_conv_repo.update_timestamp = AsyncMock()
            mock_log_repo.create = AsyncMock(return_value=mock_saved_msg)
            mock_chat_log_cls.return_value = MagicMock()

            mock_memory = MagicMock()
            mock_memory.add_user_message = AsyncMock()
            mock_memory.add_assistant_message = AsyncMock()
            mock_memory.get_memory_messages = AsyncMock(return_value=[])
            mock_memory_cls.return_value = mock_memory

            events = []
            async for event in AiChatService.handle_ai_chat_sse(
                user, "conv1", "你好", MagicMock(),
            ):
                events.append(event)

            # 应该有多个 ai_chunk 和一个 ai_complete
            event_types = []
            for event in events:
                for line in event.split("\n"):
                    if line.startswith("event: "):
                        event_types.append(line[7:])
            assert "ai_chunk" in event_types
            assert "ai_complete" in event_types
            assert "ai_error" not in event_types

    @pytest.mark.asyncio
    async def test_sse_stream_tool_call_events(self):
        """SSE 流包含工具调用事件"""
        user = self._make_user()
        mock_conv = MagicMock()
        mock_conv.userId = "user1"
        mock_conv.title = "测试"

        # 工具调用响应
        tool_call_resp = MagicMock()
        tool_call_resp.content = ""
        tool_call_resp.tool_calls = [{"name": "parseTime", "args": {"expression": "明天"}, "id": "tc_1"}]

        # 最终文本响应
        text_resp = MagicMock()
        text_resp.content = "明天是 2026-04-03"
        text_resp.tool_calls = None

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=[tool_call_resp, text_resp])
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(side_effect=[tool_call_resp, text_resp])
        mock_llm.bind_tools = MagicMock(return_value=mock_bound)

        mock_tool = MagicMock()
        mock_tool.name = "parseTime"
        mock_tool.coroutine = AsyncMock(return_value="2026-04-03")
        mock_tool.invoke = MagicMock(return_value="2026-04-03")

        mock_saved_msg = MagicMock()
        mock_saved_msg.id = "msg_tool_123"

        with patch("app.services.ai_chat_service.AiConversationRepository") as mock_conv_repo, \
             patch("app.services.ai_chat_service.ChatLogRepository") as mock_log_repo, \
             patch("app.services.ai_chat_service.ChatLog") as mock_chat_log_cls, \
             patch("app.services.ai_chat_service.MemoryManager") as mock_memory_cls, \
             patch("app.services.ai_chat_service.get_all_tools", return_value=[mock_tool]), \
             patch("app.services.ai_chat_service.build_system_prompt", return_value="测试"), \
             patch("app.services.ai_chat_service.get_chat_llm", return_value=mock_llm):
            mock_conv_repo.find_active_by_id = AsyncMock(return_value=mock_conv)
            mock_conv_repo.update_timestamp = AsyncMock()
            mock_log_repo.create = AsyncMock(return_value=mock_saved_msg)
            mock_chat_log_cls.return_value = MagicMock()

            mock_memory = MagicMock()
            mock_memory.add_user_message = AsyncMock()
            mock_memory.add_assistant_message = AsyncMock()
            mock_memory.get_memory_messages = AsyncMock(return_value=[])
            mock_memory_cls.return_value = mock_memory

            events = []
            async for event in AiChatService.handle_ai_chat_sse(
                user, "conv1", "明天几点", MagicMock(),
            ):
                events.append(event)

            event_types = []
            for event in events:
                for line in event.split("\n"):
                    if line.startswith("event: "):
                        event_types.append(line[7:])
            assert "ai_tool_call" in event_types
            assert "ai_tool_result" in event_types
            assert "ai_complete" in event_types


# ==================== WS 桥接模式测试 ====================


class TestWSBridgeMode:
    """WS 桥接模式测试：handle_ai_chat 内部消费 SSE 流"""

    def _make_user(self, user_id="user1", name="测试"):
        user = MagicMock()
        user.id = user_id
        user.name = name
        return user

    @pytest.mark.asyncio
    async def test_ws_bridge_receives_sse_events(self):
        """WS 桥接模式正确转发 SSE 事件"""
        user = self._make_user()

        # Mock SSE generator 产出一些事件
        sse_events = [
            'event: ai_chunk\ndata: {"conversationId":"conv1","content":"你好","index":1}\n\n',
            'event: ai_complete\ndata: {"conversationId":"conv1","content":"你好","messageId":"msg1"}\n\n',
        ]

        with patch.object(
            AiChatService, "handle_ai_chat_sse",
            return_value=self._async_gen(sse_events),
        ), patch("app.services.ai_chat_service.ws_manager") as mock_ws:
            mock_ws.send_to_user = AsyncMock()
            await AiChatService.handle_ai_chat(user, "conv1", "你好", None)
            # ws_manager.send_to_user 应该被调用
            assert mock_ws.send_to_user.call_count == 2
            # 验证第一个调用包含 type: ai_chunk
            first_call_data = mock_ws.send_to_user.call_args_list[0][0][1]
            assert first_call_data["type"] == "ai_chunk"
            assert first_call_data["content"] == "你好"
            # 验证第二个调用包含 type: ai_complete
            second_call_data = mock_ws.send_to_user.call_args_list[1][0][1]
            assert second_call_data["type"] == "ai_complete"

    @pytest.mark.asyncio
    async def test_ws_bridge_handles_empty_stream(self):
        """WS 桥接模式处理空流"""
        user = self._make_user()
        with patch.object(
            AiChatService, "handle_ai_chat_sse",
            return_value=self._async_gen([]),
        ), patch("app.services.ai_chat_service.ws_manager") as mock_ws:
            mock_ws.send_to_user = AsyncMock()
            await AiChatService.handle_ai_chat(user, "conv1", "你好", None)
            mock_ws.send_to_user.assert_not_called()

    @staticmethod
    async def _async_gen(items):
        """辅助：将列表转为 async generator"""
        for item in items:
            yield item

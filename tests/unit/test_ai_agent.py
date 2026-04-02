"""
AI Agent 核心循环单元测试

覆盖纯对话、工具调用、多次工具调用、工具失败、LLM 超时、最大轮次
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.agent import AgentExecutor, ToolExecutionResult, MAX_TOOL_ROUNDS


def _make_mock_llm(responses):
    """创建 Mock LLM，按顺序返回响应

    同时设置 mock_llm.ainvoke 和 mock_bound.ainvoke，
    因为 tools=[] 时 AgentExecutor 使用 llm 本身
    """
    mock_llm = MagicMock()
    mock_bound = MagicMock()
    mock_ainvoke = AsyncMock(side_effect=responses)
    mock_bound.ainvoke = mock_ainvoke
    mock_llm.ainvoke = mock_ainvoke
    mock_llm.bind_tools = MagicMock(return_value=mock_bound)
    return mock_llm, mock_bound


def _make_text_response(content: str):
    """创建纯文本响应（无工具调用）"""
    response = MagicMock()
    response.content = content
    response.tool_calls = None
    return response


def _make_tool_call_response(tool_name: str, tool_args: dict, tool_id: str = "tc_1"):
    """创建工具调用响应"""
    response = MagicMock()
    response.content = ""
    response.tool_calls = [{"name": tool_name, "args": tool_args, "id": tool_id}]
    return response


def _collect_callbacks():
    """收集 Agent 回调"""
    chunks = []
    tool_calls = []
    tool_results = []
    completes = []
    errors = []

    async def on_chunk(content, index):
        chunks.append((content, index))

    async def on_tool_call(name, args, status):
        tool_calls.append((name, args, status))

    async def on_tool_result(name, result, status):
        tool_results.append((name, result, status))

    async def on_complete(content, conv_id):
        completes.append((content, conv_id))

    async def on_error(code, msg):
        errors.append((code, msg))

    return {
        "on_chunk": on_chunk,
        "on_tool_call": on_tool_call,
        "on_tool_result": on_tool_result,
        "on_complete": on_complete,
        "on_error": on_error,
        "chunks": chunks,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "completes": completes,
        "errors": errors,
    }


def _make_executor(llm, tools=None, callbacks=None, memory=None):
    """创建测试用 AgentExecutor"""
    if tools is None:
        tools = []
    if memory is None:
        memory = []
    if callbacks is None:
        callbacks = _collect_callbacks()

    return AgentExecutor(
        llm=llm,
        tools=tools,
        system_prompt="你是测试助手",
        memory_messages=memory,
        on_chunk=callbacks["on_chunk"],
        on_tool_call=callbacks["on_tool_call"],
        on_tool_result=callbacks["on_tool_result"],
        on_complete=callbacks["on_complete"],
        on_error=callbacks["on_error"],
        conversation_id="test_conv",
    ), callbacks


# ==================== Agent 核心循环测试 ====================


class TestAgentCoreLoop:
    """TC-3 Agent 核心循环测试"""

    @pytest.mark.asyncio
    async def test_pure_conversation_no_tool(self):
        """TC-3.1: 纯对话（无工具调用）推送 ai_chunk + ai_complete"""
        text_response = _make_text_response("你好！我是 AI 助手。")
        mock_llm, _ = _make_mock_llm([text_response])

        executor, cbs = _make_executor(mock_llm)

        result = await executor.run("你好")

        assert result == "你好！我是 AI 助手。"
        assert len(cbs["chunks"]) > 0
        assert len(cbs["completes"]) == 1
        assert cbs["completes"][0][0] == "你好！我是 AI 助手。"
        assert len(cbs["errors"]) == 0

    @pytest.mark.asyncio
    async def test_single_tool_call(self):
        """TC-3.2: 单次工具调用"""
        tool_call_resp = _make_tool_call_response("parseTime", {"expression": "明天"})
        text_response = _make_text_response("明天的时间是 1743326400000")

        mock_tool = MagicMock()
        mock_tool.name = "parseTime"
        mock_tool.coroutine = AsyncMock(return_value="1743326400000 (2026-03-30 00:00:00)")
        mock_tool.invoke = MagicMock(return_value="1743326400000 (2026-03-30 00:00:00)")

        mock_llm, _ = _make_mock_llm([tool_call_resp, text_response])
        executor, cbs = _make_executor(mock_llm, tools=[mock_tool])

        result = await executor.run("明天是什么时间")

        assert "1743326400000" in result
        assert len(cbs["tool_calls"]) == 1
        assert cbs["tool_calls"][0][0] == "parseTime"
        assert cbs["tool_calls"][0][2] == "running"
        assert len(cbs["tool_results"]) == 1
        assert cbs["tool_results"][0][2] == "success"
        assert len(cbs["completes"]) == 1

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self):
        """TC-3.3: 多次工具调用（同一轮中多个 tool_call）"""
        tc1 = _make_tool_call_response("parseTime", {"expression": "明天"}, "tc_1")
        tc2 = _make_tool_call_response("getCurrentTime", {}, "tc_2")
        text_response = _make_text_response("明天和今天的时间都已查询")

        mock_tool1 = MagicMock()
        mock_tool1.name = "parseTime"
        mock_tool1.coroutine = AsyncMock(return_value="1743326400000")
        mock_tool1.invoke = MagicMock(return_value="1743326400000")

        mock_tool2 = MagicMock()
        mock_tool2.name = "getCurrentTime"
        mock_tool2.coroutine = AsyncMock(return_value="当前时间：2026-03-29")
        mock_tool2.invoke = MagicMock(return_value="当前时间：2026-03-29")

        # 同一轮返回两个 tool_call
        multi_tc_response = MagicMock()
        multi_tc_response.content = ""
        multi_tc_response.tool_calls = [
            {"name": "parseTime", "args": {"expression": "明天"}, "id": "tc_1"},
            {"name": "getCurrentTime", "args": {}, "id": "tc_2"},
        ]

        mock_llm, _ = _make_mock_llm([multi_tc_response, text_response])
        executor, cbs = _make_executor(mock_llm, tools=[mock_tool1, mock_tool2])

        result = await executor.run("查一下明天和今天的时间")

        assert len(cbs["tool_calls"]) == 2
        assert len(cbs["tool_results"]) == 2

    @pytest.mark.asyncio
    async def test_tool_execution_failure(self):
        """TC-3.4: 工具未找到"""
        tool_call_resp = _make_tool_call_response("unknownTool", {})
        text_response = _make_text_response("抱歉，该工具不可用")

        mock_llm, _ = _make_mock_llm([tool_call_resp, text_response])
        executor, cbs = _make_executor(mock_llm, tools=[])

        await executor.run("使用一个不存在的工具")

        assert len(cbs["tool_results"]) == 1
        assert cbs["tool_results"][0][2] == "error"
        assert "未找到工具" in cbs["tool_results"][0][1]

    @pytest.mark.asyncio
    async def test_llm_exception(self):
        """TC-3.5: LLM 超时/异常"""
        mock_llm, _ = _make_mock_llm([])
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API timeout"))
        # 也需要更新 bind_tools 返回的 mock
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(side_effect=Exception("API timeout"))
        mock_llm.bind_tools = MagicMock(return_value=mock_bound)

        executor, cbs = _make_executor(mock_llm)

        result = await executor.run("你好")

        assert len(cbs["errors"]) == 1
        assert cbs["errors"][0][0] == "AI_SERVICE_ERROR"
        assert "timeout" in cbs["errors"][0][1]

    @pytest.mark.asyncio
    async def test_max_rounds_reached(self):
        """TC-3.6: 达到最大轮次"""
        tool_call_resp = _make_tool_call_response("parseTime", {"expression": "测试"}, "tc_loop")

        mock_tool = MagicMock()
        mock_tool.name = "parseTime"
        mock_tool.coroutine = AsyncMock(return_value="结果")
        mock_tool.invoke = MagicMock(return_value="结果")

        # 不断返回工具调用
        mock_llm, _ = _make_mock_llm([tool_call_resp] * (MAX_TOOL_ROUNDS + 2))

        executor, cbs = _make_executor(mock_llm, tools=[mock_tool])

        await executor.run("循环测试")

        assert len(cbs["errors"]) == 1
        assert "轮次过多" in cbs["errors"][0][1]

    @pytest.mark.asyncio
    async def test_message_too_long(self):
        """补充：消息过长"""
        mock_llm, _ = _make_mock_llm([])
        executor, cbs = _make_executor(mock_llm)

        long_message = "a" * 5000
        result = await executor.run(long_message)

        assert len(cbs["errors"]) == 1
        assert cbs["errors"][0][0] == "MESSAGE_TOO_LONG"
        assert result == ""

    @pytest.mark.asyncio
    async def test_memory_messages_included(self):
        """补充：记忆消息被包含在请求中"""
        text_response = _make_text_response("好的")
        mock_llm, mock_bound = _make_mock_llm([text_response])

        memory = [
            {"role": "user", "content": "之前的问题"},
            {"role": "assistant", "content": "之前的回答"},
        ]
        executor, cbs = _make_executor(mock_llm, memory=memory)

        await executor.run("新问题")

        mock_bound.ainvoke.assert_called_once()
        call_args = mock_bound.ainvoke.call_args[0][0]
        # 检查消息列表包含系统提示词 + 记忆 + 用户消息
        assert len(call_args) >= 4

    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """补充：异步工具执行"""
        tool_call_resp = _make_tool_call_response("createTodo", {"title": "测试"})
        text_response = _make_text_response("待办已创建")

        mock_tool = MagicMock()
        mock_tool.name = "createTodo"
        mock_tool.coroutine = AsyncMock(return_value="待办创建成功")
        mock_tool.invoke = MagicMock(return_value="待办创建成功")

        mock_llm, _ = _make_mock_llm([tool_call_resp, text_response])
        executor, cbs = _make_executor(mock_llm, tools=[mock_tool])

        result = await executor.run("帮我创建待办")

        mock_tool.coroutine.assert_called_once()
        assert cbs["tool_results"][0][2] == "success"

    @pytest.mark.asyncio
    async def test_empty_response(self):
        """补充：LLM 返回空内容"""
        text_response = _make_text_response("")
        mock_llm, _ = _make_mock_llm([text_response])

        executor, cbs = _make_executor(mock_llm)

        result = await executor.run("你好")

        assert result == ""
        assert len(cbs["completes"]) == 1
        assert cbs["completes"][0][0] == ""

    @pytest.mark.asyncio
    async def test_tool_type_error(self):
        """补充：工具参数类型错误"""
        tool_call_resp = _make_tool_call_response("myTool", {"bad": "args"})
        text_response = _make_text_response("工具调用失败")

        mock_tool = MagicMock()
        mock_tool.name = "myTool"
        mock_tool.coroutine = AsyncMock(side_effect=TypeError("missing required arg"))

        mock_llm, _ = _make_mock_llm([tool_call_resp, text_response])
        executor, cbs = _make_executor(mock_llm, tools=[mock_tool])

        await executor.run("调用工具")

        assert len(cbs["tool_results"]) == 1
        assert cbs["tool_results"][0][2] == "error"
        assert "参数错误" in cbs["tool_results"][0][1]


class TestToolExecutionResult:
    """工具执行结果测试"""

    def test_success_result(self):
        """成功结果"""
        result = ToolExecutionResult(True, "操作成功")
        assert result.success is True
        assert result.result == "操作成功"

    def test_failure_result(self):
        """失败结果"""
        result = ToolExecutionResult(False, "执行错误")
        assert result.success is False
        assert result.result == "执行错误"

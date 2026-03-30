"""
AI Agent 核心循环

手动实现 ReAct（Reasoning + Acting）循环：
1. 调用 LLM，流式推送 ai_chunk
2. 如果 LLM 返回 tool_call -> 执行工具，推送通知，结果回传 LLM
3. 如果 LLM 返回最终回答 -> 推送 ai_complete
4. 超过最大轮次则终止
"""
import logging
from typing import List, Callable, Awaitable, Tuple

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# 最大工具调用轮次（可配置）
MAX_TOOL_ROUNDS = getattr(settings, "AI_MAX_TOOL_ROUNDS", 10)

# 用户消息最大长度
MAX_MESSAGE_LENGTH = 4000

# 流式输出分片大小
CHUNK_SIZE = 10


class ToolExecutionResult:
    """工具执行结果"""
    def __init__(self, success: bool, result: str):
        self.success = success
        self.result = result


class AgentExecutor:
    """
    Agent 执行器

    执行 ReAct 循环，通过回调函数推送 WebSocket 消息
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        tools: List[BaseTool],
        system_prompt: str,
        memory_messages: List[dict],
        on_chunk: Callable[[str, int], Awaitable[None]],
        on_tool_call: Callable[[str, dict, str], Awaitable[None]],
        on_tool_result: Callable[[str, str, str], Awaitable[None]],
        on_complete: Callable[[str, str], Awaitable[None]],
        on_error: Callable[[str, str], Awaitable[None]],
        conversation_id: str,
    ):
        """
        初始化 Agent 执行器

        Args:
            llm: ChatOpenAI 实例
            tools: 工具列表
            system_prompt: 系统提示词
            memory_messages: 记忆消息列表
            on_chunk: 流式片段回调 (content, index)
            on_tool_call: 工具调用通知回调 (tool_name, args, status)
            on_tool_result: 工具结果回调 (tool_name, result, status)
            on_complete: 完成回调 (full_content, conversation_id)
            on_error: 错误回调 (error_code, message)
            conversation_id: 会话 ID
        """
        self._llm = llm.bind_tools(tools) if tools else llm
        self._tools = {tool.name: tool for tool in tools}
        self._system_prompt = system_prompt
        self._memory_messages = memory_messages
        self._on_chunk = on_chunk
        self._on_tool_call = on_tool_call
        self._on_tool_result = on_tool_result
        self._on_complete = on_complete
        self._on_error = on_error
        self._conversation_id = conversation_id

    async def run(self, user_message: str) -> str:
        """
        执行 Agent 对话循环

        使用 ainvoke 处理工具调用轮次，astream 处理最终文本响应

        Args:
            user_message: 用户消息内容

        Returns:
            AI 的完整响应文本
        """
        # 消息长度验证
        if len(user_message) > MAX_MESSAGE_LENGTH:
            await self._on_error("MESSAGE_TOO_LONG", f"消息过长，最多 {MAX_MESSAGE_LENGTH} 字符")
            return ""
        messages = self._build_messages(user_message)
        full_response = ""
        for round_num in range(MAX_TOOL_ROUNDS + 1):
            try:
                # 非流式调用以可靠获取 tool_calls
                response = await self._llm.ainvoke(messages)
                # 检查是否有工具调用
                tool_calls = getattr(response, "tool_calls", None)
                if tool_calls:
                    # 将 AI 响应（含 tool_calls）加入消息历史
                    messages.append(response)
                    # 逐个执行工具
                    for tc in tool_calls:
                        tool_name = tc["name"]
                        tool_args = tc["args"]
                        tool_id = tc["id"]
                        # 通知客户端工具调用开始
                        await self._on_tool_call(tool_name, tool_args, "running")
                        # 执行工具
                        exec_result = await self._execute_tool(tool_name, tool_args)
                        # 通知客户端工具执行结果
                        result_status = "success" if exec_result.success else "error"
                        await self._on_tool_result(tool_name, exec_result.result, result_status)
                        # 将结果回传给 LLM
                        messages.append(ToolMessage(content=exec_result.result, tool_call_id=tool_id))
                else:
                    # 没有工具调用，这是最终回答
                    full_response = response.content or ""
                    # 流式推送最终回答（按字符分片模拟流式效果）
                    if full_response:
                        chunk_index = 0
                        for i in range(0, len(full_response), CHUNK_SIZE):
                            chunk_index += 1
                            await self._on_chunk(full_response[i:i + CHUNK_SIZE], chunk_index)
                    await self._on_complete(full_response, self._conversation_id)
                    return full_response
            except Exception as e:
                logger.error(f"Agent 循环异常: round={round_num}, error={e}")
                await self._on_error("AI_SERVICE_ERROR", f"AI 处理异常: {str(e)}")
                return full_response or ""
        # 超过最大轮次
        logger.warning(f"Agent 达到最大轮次: {MAX_TOOL_ROUNDS}")
        await self._on_error("AI_SERVICE_ERROR", "对话轮次过多，请简化您的问题后重试")
        return full_response

    def _build_messages(self, user_message: str) -> List:
        """
        构建发送给 LLM 的消息列表

        Args:
            user_message: 用户消息

        Returns:
            消息列表
        """
        messages = [SystemMessage(content=self._system_prompt)]
        # 添加记忆消息
        for msg in self._memory_messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                # 非法角色记录警告但不中断
                if role is not None:
                    logger.warning(f"未知的消息角色: {role}, 已跳过")
        # 添加当前用户消息
        messages.append(HumanMessage(content=user_message))
        return messages

    async def _execute_tool(self, tool_name: str, tool_args: dict) -> ToolExecutionResult:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            ToolExecutionResult 包含执行状态和结果
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolExecutionResult(False, f"未找到工具: {tool_name}")
        try:
            # 参数基本验证：确保参数是字典
            if not isinstance(tool_args, dict):
                tool_args = {}
            if tool.coroutine:
                result = await tool.coroutine(**tool_args)
            else:
                result = tool.invoke(tool_args)
            return ToolExecutionResult(True, str(result))
        except TypeError as e:
            # 参数类型错误
            logger.error(f"工具参数错误: tool={tool_name}, args={tool_args}, error={e}")
            return ToolExecutionResult(False, f"参数错误: {str(e)}")
        except Exception as e:
            logger.error(f"工具执行异常: tool={tool_name}, args={tool_args}, error={e}")
            return ToolExecutionResult(False, f"执行错误: {str(e)}")
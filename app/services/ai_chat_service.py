"""
AI 对话编排服务

编排 Agent + Memory + Tools，处理完整的 AI 对话流程。
支持 SSE 流式响应（独立对话页面）和 WebSocket 推送（群聊 @AI）两种模式。
"""
import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Optional

from redis.asyncio import Redis

from app.ai.agent import AgentExecutor
from app.ai.llm import get_chat_llm
from app.ai.memory.memory_manager import MemoryManager
from app.ai.prompts.system_prompt import build_system_prompt
from app.ai.tools.registry import get_all_tools
from app.models.chat_log import ChatLog
from app.models.user import User
from app.repository.ai_conversation_repository import AiConversationRepository
from app.repository.chat_log_repository import ChatLogRepository
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

# AI 对话 chatType
CHAT_TYPE_AI = 3

# AI 发送者 ID
AI_SENDER_ID = "ai"


class AiChatService:
    """
    AI 对话编排服务

    处理从用户消息到 AI 响应的完整流程
    """

    @staticmethod
    async def handle_ai_chat_sse(
        user: User,
        conversation_id: str,
        content: str,
        redis_client: Optional[Redis],
    ) -> AsyncGenerator[str, None]:
        """
        SSE 流式处理 AI 对话（独立对话页面使用）

        通过 async generator yield SSE 格式事件，供 FastAPI StreamingResponse 使用。
        使用 asyncio.Queue 将 Agent 回调数据传递给 generator。

        Args:
            user: 当前用户
            conversation_id: 会话 ID
            content: 用户消息内容
            redis_client: Redis 客户端

        Yields:
            str: SSE 格式事件字符串 "event: xxx\\ndata: {...}\\n\\n"
        """
        user_id = str(user.id)
        user_name = user.name
        queue: asyncio.Queue = asyncio.Queue()
        # 用于标记 Agent 执行结束
        sentinel = object()
        try:
            # 1. 验证会话
            conversation = await AiConversationRepository.find_active_by_id(conversation_id)
            if not conversation:
                yield _sse_event("ai_error", {
                    "conversationId": conversation_id,
                    "error": "CONVERSATION_NOT_FOUND",
                    "message": "会话不存在或已删除",
                })
                return
            if conversation.userId != user_id:
                yield _sse_event("ai_error", {
                    "conversationId": conversation_id,
                    "error": "FORBIDDEN",
                    "message": "无权访问该会话",
                })
                return
            # 2. 保存用户消息到 ChatLog
            current_time = int(time.time() * 1000)
            user_chat_log = ChatLog(
                conversationId=conversation_id,
                sendId=user_id,
                recvId=AI_SENDER_ID,
                chatType=CHAT_TYPE_AI,
                msgContent=content,
                sendTime=current_time,
            )
            await ChatLogRepository.create(user_chat_log)
            # 3. 如果会话无标题，用首条消息生成标题
            if not conversation.title:
                title = content[:50] if len(content) > 50 else content
                await AiConversationRepository.update_title(conversation_id, title)
            # 4. 更新会话时间戳
            await AiConversationRepository.update_timestamp(conversation_id)
            # 5. 添加用户消息到记忆缓冲
            memory = MemoryManager(redis_client)
            await memory.add_user_message(conversation_id, content)
            # 6. 获取记忆
            memory_messages = await memory.get_memory_messages(conversation_id)
            # 7. 构建工具列表
            tools = get_all_tools(user_id, user_name)
            # 8. 构建系统提示词
            system_prompt = build_system_prompt(user_id, user_name)
            # 9. 获取 LLM 实例
            llm = get_chat_llm(streaming=True)
            # 10. 用于存储 AI 响应（由 on_complete 回调写入）
            ai_response_holder = {"content": ""}

            async def on_chunk(chunk_content: str, index: int):
                await queue.put(_sse_event("ai_chunk", {
                    "conversationId": conversation_id,
                    "content": chunk_content,
                    "index": index,
                }))

            async def on_tool_call(tool_name: str, args: dict, status: str):
                await queue.put(_sse_event("ai_tool_call", {
                    "conversationId": conversation_id,
                    "tool": tool_name,
                    "args": args,
                    "status": status,
                }))

            async def on_tool_result(tool_name: str, result: str, status: str):
                await queue.put(_sse_event("ai_tool_result", {
                    "conversationId": conversation_id,
                    "tool": tool_name,
                    "result": result,
                    "status": status,
                }))

            async def on_complete(complete_content: str, conv_id: str):
                ai_response_holder["content"] = complete_content
                # 保存 AI 响应到 ChatLog
                ai_chat_log = ChatLog(
                    conversationId=conv_id,
                    sendId=AI_SENDER_ID,
                    recvId=user_id,
                    chatType=CHAT_TYPE_AI,
                    msgContent=complete_content,
                    sendTime=int(time.time() * 1000),
                )
                saved = await ChatLogRepository.create(ai_chat_log)
                await queue.put(_sse_event("ai_complete", {
                    "conversationId": conv_id,
                    "content": complete_content,
                    "messageId": str(saved.id),
                }))

            async def on_error(error_code: str, error_msg: str):
                await queue.put(_sse_event("ai_error", {
                    "conversationId": conversation_id,
                    "error": error_code,
                    "message": error_msg,
                }))

            # 11. 在后台任务中运行 Agent，通过 queue 传递事件
            async def _run_agent():
                try:
                    executor = AgentExecutor(
                        llm=llm,
                        tools=tools,
                        system_prompt=system_prompt,
                        memory_messages=memory_messages,
                        on_chunk=on_chunk,
                        on_tool_call=on_tool_call,
                        on_tool_result=on_tool_result,
                        on_complete=on_complete,
                        on_error=on_error,
                        conversation_id=conversation_id,
                    )
                    await executor.run(content)
                except Exception as e:
                    logger.error(f"Agent 执行异常: {e}", exc_info=True)
                    await queue.put(_sse_event("ai_error", {
                        "conversationId": conversation_id,
                        "error": "AI_SERVICE_ERROR",
                        "message": "AI 服务暂时不可用，请稍后重试",
                    }))
                finally:
                    await queue.put(sentinel)

            agent_task = asyncio.create_task(_run_agent())
            # 12. 从 queue 中 yield SSE 事件
            try:
                while True:
                    item = await queue.get()
                    if item is sentinel:
                        break
                    yield item
            finally:
                # 确保任务完成（如果客户端中途断开）
                if not agent_task.done():
                    agent_task.cancel()
                    try:
                        await agent_task
                    except asyncio.CancelledError:
                        pass
            # 13. 添加 AI 响应到记忆缓冲
            if ai_response_holder["content"]:
                await memory.add_assistant_message(conversation_id, ai_response_holder["content"])
        except Exception as e:
            logger.error(f"AI 对话 SSE 处理异常: conversationId={conversation_id}, error={e}", exc_info=True)
            yield _sse_event("ai_error", {
                "conversationId": conversation_id,
                "error": "AI_SERVICE_ERROR",
                "message": "AI 服务暂时不可用，请稍后重试",
            })

    @staticmethod
    async def handle_ai_chat(
        user: User,
        conversation_id: str,
        content: str,
        redis_client: Optional[Redis],
    ) -> None:
        """
        处理 AI 对话消息（WebSocket 推送模式，群聊 @AI 使用）

        内部消费 SSE 流，将事件通过 WebSocket 推送给用户。
        Args:
            user: 当前用户
            conversation_id: 会话 ID
            content: 用户消息内容
            redis_client: Redis 客户端
        """
        user_id = str(user.id)
        async for sse_data in AiChatService.handle_ai_chat_sse(
            user, conversation_id, content, redis_client,
        ):
            # 解析 SSE 事件，通过 WS 推送
            try:
                # sse_data 格式: "event: xxx\ndata: {...}\n\n"
                lines = sse_data.strip().split("\n")
                event_type = None
                event_data = None
                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:]
                    elif line.startswith("data: "):
                        event_data = json.loads(line[6:])
                if event_type and event_data:
                    event_data["type"] = event_type
                    await ws_manager.send_to_user(user_id, event_data)
            except Exception as e:
                logger.error(f"WS 推送 SSE 事件失败: {e}")


def _sse_event(event: str, data: dict) -> str:
    """
    格式化 SSE 事件字符串

    Args:
        event: 事件类型
        data: 事件数据

    Returns:
        str: SSE 格式字符串 "event: xxx\\ndata: {...}\\n\\n"
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

"""
AI 对话编排服务

编排 Agent + Memory + Tools + WebSocket 推送，处理完整的 AI 对话流程
"""
import logging
import time
from typing import Optional

from redis.asyncio import Redis

from app.ai.agent import AgentExecutor
from app.ai.llm import get_chat_llm
from app.ai.memory.memory_manager import MemoryManager
from app.ai.prompts.system_prompt import build_system_prompt
from app.ai.tools.registry import get_all_tools
from app.config.exceptions import BusinessValidationException
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
    async def handle_ai_chat(
        user: User,
        conversation_id: str,
        content: str,
        redis_client: Optional[Redis],
    ) -> None:
        """
        处理 AI 对话消息（异步任务，不阻塞 WebSocket 主循环）

        Args:
            user: 当前用户
            conversation_id: 会话 ID
            content: 用户消息内容
            redis_client: Redis 客户端
        """
        user_id = str(user.id)
        user_name = user.name
        try:
            # 1. 验证会话
            conversation = await AiConversationRepository.find_active_by_id(conversation_id)
            if not conversation:
                await _send_ai_error(user_id, conversation_id, "CONVERSATION_NOT_FOUND", "会话不存在或已删除")
                return
            if conversation.userId != user_id:
                await _send_ai_error(user_id, conversation_id, "FORBIDDEN", "无权访问该会话")
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
            # 10. 创建并运行 Agent
            # 用于存储 AI 响应（由 on_complete 回调写入）
            ai_response_holder = {"content": ""}

            async def on_chunk(chunk_content: str, index: int):
                await ws_manager.send_to_user(user_id, {
                    "type": "ai_chunk",
                    "conversationId": conversation_id,
                    "content": chunk_content,
                    "index": index,
                })

            async def on_tool_call(tool_name: str, args: dict, status: str):
                await ws_manager.send_to_user(user_id, {
                    "type": "ai_tool_call",
                    "conversationId": conversation_id,
                    "tool": tool_name,
                    "args": args,
                    "status": status,
                })

            async def on_tool_result(tool_name: str, result: str, status: str):
                await ws_manager.send_to_user(user_id, {
                    "type": "ai_tool_result",
                    "conversationId": conversation_id,
                    "tool": tool_name,
                    "result": result,
                    "status": status,
                })

            async def on_complete(complete_content: str, conv_id: str):
                # 保存完整响应
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
                # 发送完成消息
                await ws_manager.send_to_user(user_id, {
                    "type": "ai_complete",
                    "conversationId": conv_id,
                    "content": complete_content,
                    "messageId": str(saved.id),
                })

            async def on_error(error_code: str, error_msg: str):
                await _send_ai_error(user_id, conversation_id, error_code, error_msg)

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
            # 11. 添加 AI 响应到记忆缓冲
            if ai_response_holder["content"]:
                await memory.add_assistant_message(conversation_id, ai_response_holder["content"])
        except Exception as e:
            logger.error(f"AI 对话处理异常: conversationId={conversation_id}, error={e}", exc_info=True)
            await _send_ai_error(user_id, conversation_id, "AI_SERVICE_ERROR", "AI 服务暂时不可用，请稍后重试")


async def _send_ai_error(user_id: str, conversation_id: str, error_code: str, message: str) -> None:
    """
    发送 AI 错误消息给用户

    Args:
        user_id: 用户 ID
        conversation_id: 会话 ID
        error_code: 错误码
        message: 错误消息
    """
    try:
        await ws_manager.send_to_user(user_id, {
            "type": "ai_error",
            "conversationId": conversation_id,
            "error": error_code,
            "message": message,
        })
    except Exception as e:
        logger.error(f"发送 AI 错误消息失败: {e}")
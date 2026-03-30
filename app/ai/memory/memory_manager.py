"""
多会话记忆管理器

管理 AI 对话的上下文记忆，包括：
- 获取记忆（摘要 + 最近对话）
- 添加消息到缓冲
- 触发摘要压缩
- MongoDB 兜底加载
"""
import logging
from typing import List, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.ai.llm import get_summary_llm
from app.ai.memory.summary_buffer import SummaryBuffer
from app.ai.prompts.system_prompt import build_summary_prompt
from app.repository.ai_summary_repository import AiSummaryRepository
from app.repository.chat_log_repository import ChatLogRepository

logger = logging.getLogger(__name__)

# AI 对话的 chatType
CHAT_TYPE_AI = 3


class MemoryManager:
    """
    多会话记忆管理器

    每个会话维护独立的上下文记忆，通过 Redis 缓冲和 MongoDB 持久化
    """

    def __init__(self, redis_client):
        """
        初始化记忆管理器

        Args:
            redis_client: Redis 异步客户端
        """
        self._buffer = SummaryBuffer(redis_client)

    async def get_memory_messages(self, conversation_id: str) -> List[dict]:
        """
        获取会话的记忆消息列表（摘要 + 最近对话）

        优先从 Redis 读取，未命中则从 MongoDB 兜底加载

        Args:
            conversation_id: 会话 ID

        Returns:
            消息列表（格式: [{"role": "user", "content": "..."}]）
        """
        messages = []
        # 1. 获取摘要
        summary = await self._get_summary(conversation_id)
        if summary:
            messages.append({"role": "system", "content": f"[对话摘要]\n{summary}"})
        # 2. 获取最近对话缓冲
        buffer_messages = await self._buffer.get_buffer_messages(conversation_id)
        if not buffer_messages:
            # Redis 缓冲为空，尝试从 MongoDB 兜底加载最近 20 条
            buffer_messages = await self._load_from_mongodb(conversation_id)
            if buffer_messages:
                # 回写到 Redis 缓冲
                for msg in buffer_messages:
                    await self._buffer.add_message(
                        conversation_id, msg["role"], msg["content"],
                    )
        messages.extend(buffer_messages)
        return messages

    async def add_user_message(self, conversation_id: str, content: str) -> None:
        """
        添加用户消息到缓冲

        Args:
            conversation_id: 会话 ID
            content: 用户消息内容
        """
        await self._buffer.add_message(conversation_id, "user", content)

    async def add_assistant_message(self, conversation_id: str, content: str) -> None:
        """
        添加 AI 响应消息到缓冲，并检查是否需要触发摘要压缩

        Args:
            conversation_id: 会话 ID
            content: AI 响应内容
        """
        char_count = await self._buffer.add_message(conversation_id, "assistant", content)
        # 检查是否需要摘要压缩
        if self._buffer.should_trigger_summary(char_count):
            await self._trigger_summary(conversation_id)

    async def _get_summary(self, conversation_id: str) -> Optional[str]:
        """
        获取摘要，Redis 优先，MongoDB 兜底

        Args:
            conversation_id: 会话 ID

        Returns:
            摘要文本或 None
        """
        # 先从 Redis 获取
        summary = await self._buffer.get_summary(conversation_id)
        if summary:
            return summary
        # Redis 未命中，从 MongoDB 加载
        summary_doc = await AiSummaryRepository.find_by_conversation_id(conversation_id)
        if summary_doc:
            # 回写到 Redis
            await self._buffer.set_summary(conversation_id, summary_doc.summary)
            return summary_doc.summary
        return None

    async def _load_from_mongodb(self, conversation_id: str) -> List[dict]:
        """
        从 MongoDB 兜底加载最近对话

        Args:
            conversation_id: 会话 ID

        Returns:
            消息列表
        """
        chat_logs, _ = await ChatLogRepository.find_by_conditions(
            conversation_id=conversation_id,
            chat_type=CHAT_TYPE_AI,
            page=1,
            page_size=20,
        )
        if not chat_logs:
            return []
        # 按时间升序排列并转换为消息格式
        chat_logs.sort(key=lambda x: x.sendTime)
        messages = []
        for log in chat_logs:
            role = "user" if log.sendId != "ai" else "assistant"
            messages.append({"role": role, "content": log.msgContent})
        return messages

    async def _trigger_summary(self, conversation_id: str) -> None:
        """
        触发摘要压缩

        将当前摘要 + 缓冲对话发送给 LLM 生成新摘要

        Args:
            conversation_id: 会话 ID
        """
        logger.info(f"触发摘要压缩: conversationId={conversation_id}")
        try:
            # 获取当前摘要和缓冲消息
            current_summary = await self._get_summary(conversation_id)
            buffer_messages = await self._buffer.get_buffer_messages(conversation_id)
            if not buffer_messages:
                return
            # 构建摘要请求
            messages_for_summary = []
            messages_for_summary.append(SystemMessage(content=build_summary_prompt()))
            if current_summary:
                messages_for_summary.append(
                    HumanMessage(content=f"当前摘要：\n{current_summary}\n\n以下是新的对话内容：")
                )
            # 添加缓冲对话
            for msg in buffer_messages:
                if msg["role"] == "user":
                    messages_for_summary.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages_for_summary.append(AIMessage(content=msg["content"]))
            if not current_summary:
                # 首次摘要，添加提示
                messages_for_summary.append(
                    HumanMessage(content="请为以上对话生成摘要。")
                )
            # 调用 LLM 生成摘要
            llm = get_summary_llm()
            response = await llm.ainvoke(messages_for_summary)
            new_summary = response.content
            # 计算字符数
            char_count = sum(len(msg["content"]) for msg in buffer_messages)
            # 保存到 MongoDB
            await AiSummaryRepository.upsert(conversation_id, new_summary, char_count)
            # 更新 Redis 摘要缓存
            await self._buffer.set_summary(conversation_id, new_summary)
            # 清空 Redis 缓冲
            await self._buffer.clear_buffer(conversation_id)
            logger.info(
                f"摘要压缩完成: conversationId={conversation_id}, "
                f"charCount={char_count}, summaryLen={len(new_summary)}"
            )
        except Exception as e:
            logger.error(f"摘要生成失败，启用降级策略: {e}")
            # 降级：只保留最近 10 条消息
            await self._buffer.keep_recent_messages(conversation_id, 10)

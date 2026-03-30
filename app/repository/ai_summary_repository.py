"""
AI 摘要数据访问层

提供 AI 对话摘要相关的数据库操作方法
"""
import logging
from typing import Optional

from app.models.ai_summary import AiSummary

logger = logging.getLogger(__name__)


class AiSummaryRepository:
    """
    AI 摘要数据访问层

    封装所有 AI 摘要相关的数据库操作
    """

    @staticmethod
    async def create(summary: AiSummary) -> AiSummary:
        """
        创建摘要记录

        Args:
            summary: AiSummary 实体对象

        Returns:
            创建后的 AiSummary 对象
        """
        await summary.insert()
        logger.info(f"AI 摘要创建成功: conversationId={summary.conversationId}")
        return summary

    @staticmethod
    async def find_by_conversation_id(conversation_id: str) -> Optional[AiSummary]:
        """
        根据会话 ID 查询摘要

        Args:
            conversation_id: 会话 ID

        Returns:
            AiSummary 对象或 None
        """
        return await AiSummary.find_one(
            AiSummary.conversationId == conversation_id,
        )

    @staticmethod
    async def upsert(conversation_id: str, summary_text: str, char_count: int) -> AiSummary:
        """
        创建或更新摘要

        Args:
            conversation_id: 会话 ID
            summary_text: 摘要内容
            char_count: 对话字符数

        Returns:
            更新后的 AiSummary 对象
        """
        existing = await AiSummaryRepository.find_by_conversation_id(conversation_id)
        if existing:
            existing.summary = summary_text
            existing.charCount = char_count
            existing.update_timestamp()
            await existing.save()
            logger.info(f"AI 摘要更新: conversationId={conversation_id}, charCount={char_count}")
            return existing
        summary = AiSummary(
            conversationId=conversation_id,
            summary=summary_text,
            charCount=char_count,
        )
        return await AiSummaryRepository.create(summary)

    @staticmethod
    async def delete_by_conversation_id(conversation_id: str) -> bool:
        """
        根据会话 ID 删除摘要

        Args:
            conversation_id: 会话 ID

        Returns:
            是否删除成功
        """
        summary = await AiSummaryRepository.find_by_conversation_id(conversation_id)
        if not summary:
            return False
        await summary.delete()
        logger.info(f"AI 摘要删除成功: conversationId={conversation_id}")
        return True

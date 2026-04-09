"""
知识库文档数据访问层

提供知识库文档元数据的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId

from app.models.knowledge import KnowledgeDocument

logger = logging.getLogger(__name__)


class KnowledgeRepository:
    """
    知识库文档数据访问层

    封装所有知识库文档元数据的数据库操作
    """

    @staticmethod
    async def create(doc: KnowledgeDocument) -> KnowledgeDocument:
        """
        创建知识库文档记录

        Args:
            doc: KnowledgeDocument 实体对象

        Returns:
            创建后的 KnowledgeDocument 对象
        """
        await doc.insert()
        logger.info(f"知识库文档创建成功: id={doc.id}, filename={doc.filename}")
        return doc

    @staticmethod
    async def find_by_id(doc_id: str) -> Optional[KnowledgeDocument]:
        """
        根据 ID 查询文档

        Args:
            doc_id: 文档 ID

        Returns:
            KnowledgeDocument 对象或 None
        """
        return await KnowledgeDocument.get(PydanticObjectId(doc_id))

    @staticmethod
    async def find_by_user_id(
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[KnowledgeDocument], int]:
        """
        查询用户的文档列表（分页，按上传时间降序）

        Args:
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量

        Returns:
            (文档列表, 总数)
        """
        skip = (page - 1) * page_size
        query = KnowledgeDocument.find(KnowledgeDocument.userId == user_id)
        total = await query.count()
        docs = await query.skip(skip).limit(page_size).sort("-uploadTime").to_list()
        return docs, total

    @staticmethod
    async def find_pending_by_user(user_id: str) -> List[KnowledgeDocument]:
        """
        查询用户待处理的文档（status=0）

        Args:
            user_id: 用户 ID

        Returns:
            待处理文档列表
        """
        return await KnowledgeDocument.find(
            KnowledgeDocument.userId == user_id,
            KnowledgeDocument.status == 0,
        ).sort("-uploadTime").to_list()

    @staticmethod
    async def update_status(doc_id: str, status: int, chunk_count: int = 0) -> bool:
        """
        更新文档状态和分块数

        Args:
            doc_id: 文档 ID
            status: 新状态
            chunk_count: 分块数量

        Returns:
            是否更新成功
        """
        import time
        doc = await KnowledgeRepository.find_by_id(doc_id)
        if not doc:
            return False
        doc.status = status
        doc.chunkCount = chunk_count
        doc.updateTime = int(time.time() * 1000)
        await doc.save()
        return True

    @staticmethod
    async def delete(doc_id: str) -> bool:
        """
        删除文档记录

        Args:
            doc_id: 文档 ID

        Returns:
            是否删除成功
        """
        doc = await KnowledgeRepository.find_by_id(doc_id)
        if not doc:
            return False
        await doc.delete()
        logger.info(f"知识库文档删除成功: id={doc_id}")
        return True

"""
知识库工具

提供知识库查询和更新能力，作为 Agent 的原子工具注册到 TOOL_REGISTRY。
通过闭包注入当前用户上下文和 Redis 客户端。
"""
import logging
from typing import List, Dict, Any, Optional

from langchain_core.tools import StructuredTool, BaseTool
from pydantic import BaseModel, Field

from app.ai.tools.base import ToolProvider

logger = logging.getLogger(__name__)


class QueryKnowledgeInput(BaseModel):
    """知识库查询输入"""
    question: str = Field(..., description="用户的问题或查询关键词")


class UpdateKnowledgeInput(BaseModel):
    """知识库更新输入"""
    docIds: List[str] = Field(
        default_factory=list,
        description="要更新的文档 ID 列表，为空则更新所有待处理文档",
    )


def _make_query_knowledge(userId: str, userName: str):
    """
    知识库查询工具的工厂函数

    Args:
        userId: 当前用户 ID
        userName: 当前用户名
    """
    async def _query_knowledge(question: str) -> str:
        """
        查询知识库

        根据用户问题进行语义检索，返回最相关的文档片段

        Args:
            question: 用户的问题或查询关键词

        Returns:
            相关文档片段的拼接文本，或无结果提示
        """
        from app.ai.embedding import embed_text
        from app.ai.vectorstore.redis_store import RedisVectorStore

        try:
            # 生成查询向量
            query_embedding = await embed_text(question)
            # 从应用状态获取 Redis 客户端
            from app.config.redis import get_redis_client
            redis_client = await get_redis_client()
            if not redis_client:
                return "知识库服务暂时不可用（Redis 未连接）"

            store = RedisVectorStore(redis_client)
            results = await store.search(query_embedding)

            if not results:
                return "知识库中未找到与您问题相关的内容。建议先上传相关文档并更新知识库。"

            # 拼装检索结果
            context_parts = []
            for i, result in enumerate(results, 1):
                source = result.metadata.get("filename", "未知文档")
                context_parts.append(f"[参考{i} - 来源: {source}]\n{result.content}")

            return "\n\n---\n\n".join(context_parts)

        except ValueError as e:
            logger.warning(f"知识库查询配置错误: {e}")
            return f"知识库查询失败: {str(e)}"
        except Exception as e:
            logger.error(f"知识库查询异常: question={question}, error={e}", exc_info=True)
            return "知识库查询出现错误，请稍后重试"

    return _query_knowledge


def _make_update_knowledge(userId: str, userName: str):
    """
    知识库更新工具的工厂函数

    Args:
        userId: 当前用户 ID
        userName: 当前用户名
    """
    async def _update_knowledge(docIds: Optional[List[str]] = None) -> str:
        """
        更新知识库

        解析待处理文档，分块、向量化并存入 Redis。
        如果指定了 docIds，则只处理这些文档；否则处理所有待处理文档。

        Args:
            docIds: 要更新的文档 ID 列表

        Returns:
            更新结果摘要
        """
        from app.ai.document.parser import DocumentParser
        from app.ai.document.chunker import TextChunker
        from app.ai.embedding import embed_batch
        from app.ai.vectorstore.redis_store import RedisVectorStore
        from app.repository.knowledge_repository import KnowledgeRepository
        from app.config.redis import get_redis_client

        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return "知识库服务暂时不可用（Redis 未连接）"

            # 查找待处理文档
            if docIds:
                docs = []
                for doc_id in docIds:
                    doc = await KnowledgeRepository.find_by_id(doc_id)
                    if doc and doc.userId == userId:
                        docs.append(doc)
            else:
                docs = await KnowledgeRepository.find_pending_by_user(userId)

            if not docs:
                return "没有待处理的文档。请先上传文档文件。"

            store = RedisVectorStore(redis_client)
            await store.create_index()

            success_count = 0
            fail_count = 0
            total_chunks = 0

            for doc in docs:
                try:
                    # 解析文档
                    text = DocumentParser.parse(doc.filepath)
                    # 分块
                    chunks = TextChunker.chunk(
                        text,
                        metadata={"filename": doc.filename, "doc_id": str(doc.id)},
                    )
                    if not chunks:
                        await KnowledgeRepository.update_status(str(doc.id), status=2)
                        fail_count += 1
                        continue

                    # 删除旧块（如果存在重新处理的情况）
                    await store.delete_by_doc_id(str(doc.id))

                    # 批量向量化
                    texts = [c["content"] for c in chunks]
                    embeddings = await embed_batch(texts)

                    # 存入 Redis
                    added = await store.add_documents(str(doc.id), chunks, embeddings)

                    # 更新文档状态
                    await KnowledgeRepository.update_status(
                        str(doc.id), status=1, chunk_count=added,
                    )
                    success_count += 1
                    total_chunks += added
                    logger.info(f"文档处理成功: {doc.filename}, chunks={added}")

                except Exception as e:
                    logger.error(f"文档处理失败: {doc.filename}, error={e}", exc_info=True)
                    await KnowledgeRepository.update_status(str(doc.id), status=2)
                    fail_count += 1

            result_parts = [f"知识库更新完成: 成功 {success_count} 个文档"]
            if fail_count > 0:
                result_parts.append(f"失败 {fail_count} 个")
            result_parts.append(f"共生成 {total_chunks} 个知识块")

            return "，".join(result_parts) + "。现在您可以向我提问关于文档内容的问题了。"

        except ValueError as e:
            logger.warning(f"知识库更新配置错误: {e}")
            return f"知识库更新失败: {str(e)}"
        except Exception as e:
            logger.error(f"知识库更新异常: userId={userId}, error={e}", exc_info=True)
            return "知识库更新出现错误，请稍后重试"

    return _update_knowledge


class KnowledgeToolProvider(ToolProvider):
    """知识库工具提供者"""

    name = "knowledge"
    description = "知识库查询和更新工具"
    requires_context = True
    category = "knowledge"

    def get_tools(
        self,
        user_id: str = None,
        user_name: str = None,
        context: Dict[str, Any] = None,
    ) -> List[BaseTool]:
        """
        获取知识库工具列表

        Args:
            user_id: 当前用户 ID
            user_name: 当前用户名
            context: 额外上下文信息（未使用）

        Returns:
            工具列表
        """
        if not user_id or not user_name:
            return []
        return [
            StructuredTool.from_function(
                coroutine=_make_query_knowledge(user_id, user_name),
                name="queryKnowledge",
                description=(
                    "查询企业内部知识库。根据用户的问题进行语义检索，返回最相关的文档片段。"
                    "适用于回答关于规章制度、操作手册、员工手册等企业文档的问题。"
                    "当用户询问公司制度、流程规范、操作指南等问题时使用此工具。"
                ),
                args_schema=QueryKnowledgeInput,
            ),
            StructuredTool.from_function(
                coroutine=_make_update_knowledge(user_id, user_name),
                name="updateKnowledge",
                description=(
                    "根据上传的文档更新知识库。解析文档、分块、向量化并存入知识库。"
                    "当用户要求更新知识库、导入文档内容、或者上传了新文件后使用此工具。"
                    "可以指定文档 ID 列表，或留空处理所有待处理文档。"
                ),
                args_schema=UpdateKnowledgeInput,
            ),
        ]


# 模块导入时自动注册
KnowledgeToolProvider().register()

"""
Redis RediSearch 向量存储

封装 FT.CREATE / FT.SEARCH / HSET / HGETALL 等操作，
提供知识库文档向量的存储、检索和管理能力。
"""
import json
import logging
import struct
import uuid
from typing import List, Dict, Any, Optional, Tuple

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class SearchResult:
    """向量检索结果条目"""
    def __init__(self, chunk_id: str, content: str, score: float, metadata: Dict[str, Any]):
        self.chunkId = chunk_id
        self.content = content
        self.score = score
        self.metadata = metadata


class RedisVectorStore:
    """
    Redis 向量存储

    使用 RediSearch 的向量索引能力实现知识库检索。
    数据结构：Hash (knowledge:chunk:{id})
    索引字段：doc_id(TAG), content(TEXT), embedding(VECTOR), metadata(TEXT)
    """

    def __init__(self, redis_client: redis.Redis):
        """
        初始化向量存储

        Args:
            redis_client: Redis 异步客户端
        """
        self._redis = redis_client
        self._index_name = settings.KNOWLEDGE_INDEX_NAME
        self._key_prefix = settings.KNOWLEDGE_KEY_PREFIX
        self._dimensions = settings.SILICONFLOW_EMBEDDING_DIMENSIONS

    async def create_index(self) -> bool:
        """
        创建向量索引（幂等操作，已存在则跳过）

        Returns:
            是否创建成功
        """
        try:
            # 检查索引是否已存在
            indices = await self._redis.execute_command("FT._LIST")
            if self._index_name.encode() in indices or self._index_name in indices:
                logger.debug(f"向量索引已存在: {self._index_name}")
                return True
        except redis.ResponseError:
            # FT._LIST 不可用时忽略
            pass

        try:
            await self._redis.execute_command(
                "FT.CREATE", self._index_name,
                "ON", "HASH",
                "PREFIX", "1", self._key_prefix,
                "SCHEMA",
                "doc_id", "TAG",
                "content", "TEXT",
                "embedding", "VECTOR", "FLAT", "6",
                "TYPE", "FLOAT32",
                "DIM", str(self._dimensions),
                "DISTANCE_METRIC", "COSINE",
                "metadata", "TEXT",
            )
            logger.info(f"向量索引创建成功: {self._index_name}")
            return True
        except redis.ResponseError as e:
            if "Index already exists" in str(e):
                return True
            logger.error(f"创建向量索引失败: {e}")
            return False

    async def add_documents(
        self,
        doc_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """
        批量添加文档向量块

        Args:
            doc_id: 文档 ID
            chunks: 分块列表，每项含 content 和 metadata
            embeddings: 对应的向量列表

        Returns:
            成功添加的数量
        """
        if len(chunks) != len(embeddings):
            logger.error(f"分块数({len(chunks)})与向量数({len(embeddings)})不匹配")
            return 0

        count = 0
        async with self._redis.pipeline() as pipe:
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = str(uuid.uuid4())
                key = f"{self._key_prefix}{chunk_id}"
                vector_bytes = self._floats_to_bytes(embedding)
                pipe.hset(key, mapping={
                    "doc_id": doc_id,
                    "content": chunk.get("content", ""),
                    "embedding": vector_bytes,
                    "metadata": json.dumps(chunk.get("metadata", {}), ensure_ascii=False),
                })
                count += 1
                # 每 100 条执行一次
                if count % 100 == 0:
                    await pipe.execute()
                    pipe = self._redis.pipeline()
            if count % 100 != 0:
                await pipe.execute()

        logger.info(f"添加文档向量: doc_id={doc_id}, chunks={count}")
        return count

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        score_threshold: float = None,
    ) -> List[SearchResult]:
        """
        KNN 向量检索

        Args:
            query_embedding: 查询向量
            top_k: 返回数量，默认使用配置值
            score_threshold: 相似度阈值，默认使用配置值

        Returns:
            检索结果列表（按相似度降序）
        """
        top_k = top_k or settings.KNOWLEDGE_TOP_K
        score_threshold = score_threshold or settings.KNOWLEDGE_SCORE_THRESHOLD

        query_vector = self._floats_to_bytes(query_embedding)
        try:
            results = await self._redis.execute_command(
                "FT.SEARCH", self._index_name,
                f"*=>[KNN {top_k} @embedding $query_vec AS score]",
                "PARAMS", "2", "query_vec", query_vector,
                "SORTBY", "score",
                "DIALECT", "2",
                "RETURN", "3", "content", "score", "metadata",
            )
        except redis.ResponseError as e:
            logger.error(f"向量检索失败: {e}")
            return []

        return self._parse_search_results(results, score_threshold)

    async def delete_by_doc_id(self, doc_id: str) -> int:
        """
        按文档 ID 删除所有关联向量块

        Args:
            doc_id: 文档 ID

        Returns:
            删除的数量
        """
        try:
            # 通过 FT.SEARCH 查找该文档的所有块
            results = await self._redis.execute_command(
                "FT.SEARCH", self._index_name,
                f"@doc_id:{{{doc_id}}}",
                "NOCONTENT",
                "LIMIT", "0", "10000",
                "DIALECT", "2",
            )
        except redis.ResponseError as e:
            logger.error(f"查询文档块失败: doc_id={doc_id}, error={e}")
            return 0

        if not results or len(results) < 1:
            return 0

        # results[0] 是总数，之后是 key,value 交替
        total = results[0] if isinstance(results[0], int) else 0
        keys_to_delete = []
        i = 1
        while i < len(results):
            key = results[i]
            if isinstance(key, bytes):
                key = key.decode()
            if key.startswith(self._key_prefix):
                keys_to_delete.append(key)
            i += 2  # 跳过 key 和 value

        if keys_to_delete:
            await self._redis.delete(*keys_to_delete)
            logger.info(f"删除文档向量块: doc_id={doc_id}, count={len(keys_to_delete)}")

        return len(keys_to_delete)

    async def get_chunk_count(self, doc_id: str) -> int:
        """
        获取指定文档的向量块数量

        Args:
            doc_id: 文档 ID

        Returns:
            块数量
        """
        try:
            results = await self._redis.execute_command(
                "FT.SEARCH", self._index_name,
                f"@doc_id:{{{doc_id}}}",
                "NOCONTENT",
                "LIMIT", "0", "0",
                "DIALECT", "2",
            )
            return results[0] if isinstance(results[0], int) else 0
        except redis.ResponseError:
            return 0

    def _parse_search_results(
        self,
        results: list,
        score_threshold: float,
    ) -> List[SearchResult]:
        """
        解析 FT.SEARCH 返回结果

        Args:
            results: FT.SEARCH 原始返回
            score_threshold: 相似度阈值

        Returns:
            SearchResult 列表
        """
        search_results: List[SearchResult] = []
        if not results or len(results) < 3:
            return search_results

        # results 格式: [total_count, key1, {field1: val1, ...}, key2, ...]
        i = 1
        while i < len(results) - 1:
            key = results[i]
            fields = results[i + 1]
            if not isinstance(fields, dict):
                i += 2
                continue

            # 余弦距离：值越小越相似，1-距离=相似度
            raw_score = fields.get("score", b"1.0")
            if isinstance(raw_score, bytes):
                raw_score = raw_score.decode()
            score = float(raw_score)

            if score > score_threshold:
                i += 2
                continue

            content = fields.get("content", b"")
            if isinstance(content, bytes):
                content = content.decode()

            metadata_raw = fields.get("metadata", b"{}")
            if isinstance(metadata_raw, bytes):
                metadata_raw = metadata_raw.decode()
            try:
                metadata = json.loads(metadata_raw)
            except json.JSONDecodeError:
                metadata = {}

            chunk_id = key
            if isinstance(chunk_id, bytes):
                chunk_id = chunk_id.decode()
            # 去掉前缀
            chunk_id = chunk_id.replace(self._key_prefix, "")

            search_results.append(SearchResult(
                chunkId=chunk_id,
                content=content,
                score=score,
                metadata=metadata,
            ))
            i += 2

        return search_results

    @staticmethod
    def _floats_to_bytes(floats: List[float]) -> bytes:
        """
        将浮点数列表转换为 FLOAT32 字节序列

        Args:
            floats: 浮点数列表

        Returns:
            字节序列
        """
        return struct.pack(f"{len(floats)}f", *floats)

"""
文本分块器

将长文本按段落和长度策略切分为固定大小的块，
块之间保留重叠部分以确保上下文完整性。
"""
import logging
import re
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """
    文本分块器

    分块策略：
    1. 按段落（双换行符）初步切分
    2. 超长段落按固定字符数二次切分
    3. 相邻块之间保留 overlap 字符的重叠
    """

    @staticmethod
    def chunk(
        text: str,
        chunk_size: int = None,
        overlap: int = None,
        metadata: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        将文本切分为带元数据的分块

        Args:
            text: 输入文本
            chunk_size: 分块最大字符数，默认使用配置值
            overlap: 重叠字符数，默认使用配置值
            metadata: 附加到每个块的元数据（如文档名、页码等）

        Returns:
            分块列表，每项含 content 和 metadata
        """
        chunk_size = chunk_size or settings.KNOWLEDGE_CHUNK_SIZE
        overlap = overlap or settings.KNOWLEDGE_CHUNK_OVERLAP
        metadata = metadata or {}

        if not text or not text.strip():
            return []

        # 按段落切分
        paragraphs = TextChunker._split_paragraphs(text)
        # 合并段落为分块
        chunks = TextChunker._merge_paragraphs(paragraphs, chunk_size, overlap)

        # 附加元数据
        results = []
        for i, chunk_content in enumerate(chunks):
            chunk_metadata = {**metadata, "chunk_index": i}
            results.append({
                "content": chunk_content,
                "metadata": chunk_metadata,
            })

        logger.debug(f"文本分块完成: 输入长度={len(text)}, 分块数={len(results)}")
        return results

    @staticmethod
    def _split_paragraphs(text: str) -> List[str]:
        """
        按段落分隔文本

        支持多种段落分隔方式：双换行、Markdown 标题行

        Args:
            text: 原始文本

        Returns:
            段落列表（过滤空段落）
        """
        # 按双换行符分割
        raw_paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = []
        for para in raw_paragraphs:
            para = para.strip()
            if para:
                paragraphs.append(para)
        return paragraphs

    @staticmethod
    def _merge_paragraphs(
        paragraphs: List[str],
        chunk_size: int,
        overlap: int,
    ) -> List[str]:
        """
        将段落合并为不超过 chunk_size 的分块

        相邻段落会尽量合并到同一个块中，
        如果单个段落超过 chunk_size 则独立切分

        Args:
            paragraphs: 段落列表
            chunk_size: 分块最大字符数
            overlap: 重叠字符数

        Returns:
            分块文本列表
        """
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            # 单个段落超过 chunk_size，需要独立切分
            if len(para) > chunk_size:
                # 先保存当前累积的块
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                # 切分长段落
                sub_chunks = TextChunker._split_long_text(para, chunk_size, overlap)
                chunks.extend(sub_chunks)
            elif len(current_chunk) + len(para) + 2 <= chunk_size:
                # 可以合并到当前块
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    chunks.append(current_chunk)
                # 新块从上一块末尾的 overlap 部分开始
                if chunks and overlap > 0:
                    overlap_text = chunks[-1][-overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para

        # 保存最后一个块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def _split_long_text(text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        将超长文本按固定大小切分

        优先在句子边界（句号、换行）处切分

        Args:
            text: 超长文本
            chunk_size: 分块最大字符数
            overlap: 重叠字符数

        Returns:
            分块列表
        """
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
            # 在 chunk_size 范围内寻找最佳切分点
            split_pos = TextChunker._find_split_point(text, start, end)
            chunks.append(text[start:split_pos])
            # 下一块从 overlap 处开始
            start = split_pos - overlap if overlap < split_pos else split_pos

        return chunks

    @staticmethod
    def _find_split_point(text: str, start: int, end: int) -> int:
        """
        在指定范围内寻找最佳文本切分点

        优先级：句号 > 换行符 > 任意位置

        Args:
            text: 完整文本
            start: 起始位置
            end: 结束位置（最大切分位置）

        Returns:
            切分位置索引
        """
        # 在 (start + chunk_size * 0.5, end] 范围内查找
        search_start = start + (end - start) // 2
        search_range = text[search_start:end]

        # 查找句号
        for sep in ["。", ".", "！", "!", "？", "?", "；", ";"]:
            pos = search_range.rfind(sep)
            if pos != -1:
                return search_start + pos + len(sep)

        # 查找换行符
        pos = search_range.rfind("\n")
        if pos != -1:
            return search_start + pos + 1

        # 查找空格
        pos = search_range.rfind(" ")
        if pos != -1:
            return search_start + pos + 1

        # 未找到分隔符，在 end 处强制切分
        return end

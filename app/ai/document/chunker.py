"""
文本分块器

将长文本按段落和长度策略切分为固定大小的块，
块之间保留重叠部分以确保上下文完整性。
支持结构化分块（从 TextBlock 计算位置范围）和纯文本分块（向后兼容）。
"""
import logging
import re
from typing import List, Dict, Any

from app.config import settings
from app.ai.document.parser import TextBlock, ParseResult

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
        将文本切分为带元数据的分块（向后兼容）

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
    def chunk_structured(
        parse_result: ParseResult,
        chunk_size: int = None,
        metadata: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        将结构化解析结果切分为带位置信息的分块

        Args:
            parse_result: 文档解析结果（含 TextBlock 列表）
            chunk_size: 分块最大字符数，默认使用配置值
            metadata: 附加到每个块的元数据

        Returns:
            分块列表，每项含 content、metadata（含 locationLabel）
        """
        chunk_size = chunk_size or settings.KNOWLEDGE_CHUNK_SIZE
        metadata = metadata or {}
        blocks = parse_result.blocks

        if not blocks:
            return []

        # 合并 TextBlock 为分块
        merged_groups = TextChunker._merge_blocks(blocks, chunk_size)

        # 生成结果
        results = []
        for i, group in enumerate(merged_groups):
            # 拼接内容
            content = "\n\n".join(b.content for b in group)
            # 计算位置标签
            location_label = TextChunker._compute_location_label(group)
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "locationLabel": location_label,
            }
            results.append({
                "content": content,
                "metadata": chunk_metadata,
            })

        logger.debug(f"结构化分块完成: blocks={len(blocks)}, chunks={len(results)}")
        return results

    @staticmethod
    def _merge_blocks(
        blocks: List[TextBlock],
        chunk_size: int,
    ) -> List[List[TextBlock]]:
        """
        将 TextBlock 列表合并为不超过 chunk_size 的分组

        相邻 block 尽量合并到同一组，单个 block 超过 chunk_size 则独立成组

        Args:
            blocks: TextBlock 列表
            chunk_size: 分块最大字符数

        Returns:
            分组后的 TextBlock 列表
        """
        if not blocks:
            return []

        groups: List[List[TextBlock]] = []
        current_group: List[TextBlock] = []
        current_size = 0

        for block in blocks:
            block_size = len(block.content)
            # 单个 block 超过 chunk_size，独立成组
            if block_size > chunk_size and current_group:
                groups.append(current_group)
                current_group = [block]
                current_size = block_size
            elif current_size + block_size + 2 > chunk_size and current_group:
                groups.append(current_group)
                current_group = [block]
                current_size = block_size
            else:
                current_group.append(block)
                current_size += block_size + 2

        if current_group:
            groups.append(current_group)

        return groups

    @staticmethod
    def _compute_location_label(blocks: List[TextBlock]) -> str:
        """
        根据 TextBlock 列表计算人类可读的位置标签

        Args:
            blocks: 同一个 chunk 内的 TextBlock 列表

        Returns:
            位置标签字符串
        """
        if not blocks:
            return ""

        first = blocks[0]
        last = blocks[-1]

        # 全部是同页
        if first.locationType == "page":
            if first.locationValue == last.locationValue:
                return f"第{first.locationValue}页"
            return f"第{first.locationValue}-{last.locationValue}页"

        # 全部是行号
        if first.locationType == "line":
            start = first.locationValue
            end = TextChunker._find_end_line(blocks)
            if start == end:
                return f"第{start}行"
            return f"第{start}-{end}行"

        # section 类型（Word 标题段落）
        if first.locationType == "section":
            # 如果首尾 section 相同
            if first.locationValue == last.locationValue:
                return first.locationValue
            return f"{first.locationValue} - {last.locationValue}"

        # 混合或 paragraph
        return first.locationValue

    @staticmethod
    def _find_end_line(blocks: List[TextBlock]) -> str:
        """
        计算 TextBlock 列表的结束行号

        通过最后一个 block 的内容和起始行号推算

        Args:
            blocks: TextBlock 列表

        Returns:
            结束行号字符串
        """
        last = blocks[-1]
        try:
            start = int(last.locationValue)
            # 计算最后一个 block 的行数
            line_count = last.content.count("\n") + 1
            return str(start + line_count - 1)
        except (ValueError, TypeError):
            return last.locationValue

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

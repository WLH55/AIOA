"""
文档解析器

支持 PDF、Word (.docx)、TXT、Markdown 格式的文本提取。
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    文档解析器

    根据文件扩展名自动选择解析策略，提取纯文本内容。
    """

    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    @staticmethod
    def parse(file_path: str) -> str:
        """
        解析文档并提取纯文本

        Args:
            file_path: 文件路径

        Returns:
            提取的纯文本内容

        Raises:
            ValueError: 不支持的文件格式
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = path.suffix.lower()
        if ext not in DocumentParser.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}，支持: {DocumentParser.SUPPORTED_EXTENSIONS}")

        parsers = {
            ".pdf": DocumentParser._parse_pdf,
            ".docx": DocumentParser._parse_docx,
            ".txt": DocumentParser._parse_text,
            ".md": DocumentParser._parse_markdown,
        }
        parser = parsers.get(ext)
        if not parser:
            raise ValueError(f"未实现 {ext} 格式的解析器")

        logger.info(f"解析文档: {path.name} ({ext})")
        return parser(file_path)

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """
        解析 PDF 文件

        使用 pdfplumber 提取每页文本，按页码分隔

        Args:
            file_path: PDF 文件路径

        Returns:
            提取的文本内容
        """
        import pdfplumber

        pages_text = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f"[第{i + 1}页]\n{text.strip()}")

        return "\n\n".join(pages_text)

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """
        解析 Word (.docx) 文件

        提取所有段落的文本，保留标题层级

        Args:
            file_path: Word 文件路径

        Returns:
            提取的文本内容
        """
        from docx import Document

        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                # 检测标题样式
                style_name = para.style.name if para.style else ""
                if style_name.startswith("Heading"):
                    paragraphs.append(f"## {text}")
                else:
                    paragraphs.append(text)

        # 提取表格内容
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip("| "):
                    paragraphs.append(row_text)

        return "\n\n".join(paragraphs)

    @staticmethod
    def _parse_text(file_path: str) -> str:
        """
        解析纯文本文件

        Args:
            file_path: TXT 文件路径

        Returns:
            文件文本内容
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _parse_markdown(file_path: str) -> str:
        """
        解析 Markdown 文件

        直接读取文本，Markdown 格式保留作为结构信息

        Args:
            file_path: Markdown 文件路径

        Returns:
            Markdown 文本内容
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

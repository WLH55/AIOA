"""
知识库文档模型

存储上传文档的元数据（文件名、路径、状态、分块数等）。
向量数据存储在 Redis，MongoDB 仅存储文档级元数据。
"""
from typing import Optional
from beanie import Document
from pydantic import Field


class KnowledgeDocument(Document):
    """
    知识库文档

    Attributes:
        filename: 原始文件名
        filepath: 服务器存储路径
        fileSize: 文件大小（字节）
        fileType: 文件类型（pdf/docx/txt/md）
        chunkCount: 分块数量
        status: 文档状态（0=处理中, 1=已完成, 2=失败）
        userId: 上传者 ID
        uploadTime: 上传时间（毫秒时间戳）
        updateTime: 更新时间（毫秒时间戳）
    """

    filename: str
    filepath: str
    fileSize: int = 0
    fileType: str = ""
    chunkCount: int = 0
    status: int = 0
    userId: str
    uploadTime: int
    updateTime: int = 0

    class Settings:
        name = "knowledge_document"
        indexes = [
            "userId",
            "status",
        ]

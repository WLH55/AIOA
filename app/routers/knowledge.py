"""
知识库路由模块

提供知识库文件上传、文档列表、文档删除的 HTTP API 端点。
知识库对话复用 /v1/ai/chat/stream SSE 端点。
"""
import logging
import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, status, Query
from fastapi.responses import JSONResponse

from app.config import settings
from app.config.schemas import ApiResponse
from app.models.user import User
from app.repository.knowledge_repository import KnowledgeRepository
from app.security.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["知识库"])

# 确保上传目录存在
_UPLOAD_DIR = Path(settings.KNOWLEDGE_UPLOAD_DIR)
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/upload",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传知识库文档",
    description="上传 PDF/Word/TXT/Markdown 文件到知识库",
)
async def upload_file(
    file: UploadFile = File(..., description="文档文件"),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    上传知识库文档

    支持格式: .pdf, .docx, .txt, .md
    文件保存到本地 storage/knowledge/ 目录，元数据存入 MongoDB
    """
    # 验证文件格式
    filename = file.filename or ""
    # 清洗文件名：只保留安全字符，防止路径遍历
    safe_filename = Path(filename).name.replace("..", "").replace("/", "").replace("\\", "")
    ext = Path(safe_filename).suffix.lower()
    supported = {".pdf", ".docx", ".txt", ".md"}
    if ext not in supported:
        return ApiResponse.error(
            code=400,
            message=f"不支持的文件格式: {ext}，支持: {', '.join(sorted(supported))}",
        )

    # 读取文件内容
    content_bytes = await file.read()
    file_size = len(content_bytes)
    if file_size == 0:
        return ApiResponse.error(code=400, message="文件内容为空")

    if file_size > 50 * 1024 * 1024:  # 50MB 限制
        return ApiResponse.error(code=400, message="文件大小超过 50MB 限制")

    # 保存文件（使用时间戳 + 安全文件名避免重名和路径遍历）
    timestamp = int(time.time() * 1000)
    safe_name = f"{timestamp}_{safe_filename}"
    file_path = _UPLOAD_DIR / safe_name
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    # 创建文档记录
    from app.models.knowledge import KnowledgeDocument
    doc = KnowledgeDocument(
        filename=filename,
        filepath=str(file_path),
        fileSize=file_size,
        fileType=ext.lstrip("."),
        status=0,  # 待处理
        userId=str(current_user.id),
        uploadTime=timestamp,
    )
    saved = await KnowledgeRepository.create(doc)

    logger.info(f"知识库文件上传成功: {filename}, size={file_size}, user={current_user.name}")

    return ApiResponse.success(
        data={
            "id": str(saved.id),
            "filename": saved.filename,
            "fileSize": saved.fileSize,
            "fileType": saved.fileType,
            "status": saved.status,
            "uploadTime": saved.uploadTime,
        },
        message="文件上传成功，请在 AI 对话中发送指令更新知识库",
    )


@router.get(
    "/list",
    response_model=ApiResponse,
    summary="获取知识库文档列表",
    description="获取当前用户上传的知识库文档列表",
)
async def list_documents(
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    获取知识库文档列表
    """
    docs, total = await KnowledgeRepository.find_by_user_id(
        str(current_user.id), page, pageSize,
    )
    items = []
    for doc in docs:
        items.append({
            "id": str(doc.id),
            "filename": doc.filename,
            "fileSize": doc.fileSize,
            "fileType": doc.fileType,
            "chunkCount": doc.chunkCount,
            "status": doc.status,
            "uploadTime": doc.uploadTime,
            "updateTime": doc.updateTime,
        })
    return ApiResponse.success(data={"list": items, "total": total})


@router.post(
    "/delete",
    response_model=ApiResponse,
    summary="删除知识库文档",
    description="删除指定文档及其向量数据",
)
async def delete_document(
    request: dict,
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    删除知识库文档

    同时删除：文件、MongoDB 记录、Redis 向量数据
    """
    doc_id = request.get("id") if request else None
    if not doc_id:
        return ApiResponse.error(code=400, message="缺少文档 ID")

    doc = await KnowledgeRepository.find_by_id(doc_id)
    if not doc:
        return ApiResponse.error(code=404, message="文档不存在")
    if doc.userId != str(current_user.id):
        return ApiResponse.error(code=403, message="无权删除此文档")

    # 删除 Redis 中的向量数据
    try:
        from app.config.redis import get_redis_client
        from app.ai.vectorstore.redis_store import RedisVectorStore
        redis_client = await get_redis_client()
        if redis_client:
            store = RedisVectorStore(redis_client)
            await store.delete_by_doc_id(doc_id)
    except Exception as e:
        logger.warning(f"删除文档向量数据失败: {e}")

    # 删除本地文件
    try:
        file_path = Path(doc.filepath)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning(f"删除文档文件失败: {e}")

    # 删除 MongoDB 记录
    await KnowledgeRepository.delete(doc_id)

    return ApiResponse.success(message="文档删除成功")


@router.get(
    "/file/{doc_id}/content",
    response_model=ApiResponse,
    summary="获取文档解析内容",
    description="获取文档的解析文本内容，TXT/MD 带行号，PDF/Word 带页码/标题标记",
)
async def get_file_content(
    doc_id: str,
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """
    获取文档解析内容

    返回解析后的纯文本内容，用于前端弹窗预览。
    TXT/Markdown: 每行带行号前缀
    PDF: 每页带 [第X页] 标记
    Word: 每段带标题/段落标记
    """
    doc = await KnowledgeRepository.find_by_id(doc_id)
    if not doc:
        return ApiResponse.error(code=404, message="文档不存在")
    if doc.userId != str(current_user.id):
        return ApiResponse.error(code=403, message="无权访问此文档")

    # 检查文件是否存在
    file_path = Path(doc.filepath)
    if not file_path.exists():
        return ApiResponse.error(code=404, message="文件已被删除")

    try:
        from app.ai.document.parser import DocumentParser
        parse_result = DocumentParser.parse_structured(str(file_path))

        # 根据文件类型格式化输出
        if doc.fileType in ("txt", "md"):
            content = _format_with_line_numbers(parse_result.fullText)
        else:
            content = parse_result.fullText

        return ApiResponse.success(data={
            "filename": doc.filename,
            "fileType": doc.fileType,
            "content": content,
        })
    except Exception as e:
        logger.error(f"获取文档内容失败: doc_id={doc_id}, error={e}")
        return ApiResponse.error(code=500, message="文档解析失败，请稍后重试")


def _format_with_line_numbers(text: str) -> str:
    """
    为纯文本添加行号前缀

    Args:
        text: 原始文本

    Returns:
        带行号的文本
    """
    lines = text.split("\n")
    max_line_num = len(lines)
    # 计算行号宽度
    width = len(str(max_line_num))
    numbered_lines = []
    for i, line in enumerate(lines, 1):
        numbered_lines.append(f"{str(i).rjust(width)}  {line}")
    return "\n".join(numbered_lines)

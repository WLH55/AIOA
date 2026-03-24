"""
Approval 模块 DTO
"""
from app.dto.approval.approval_request import (
    ApprovalRequest,
    ApprovalListRequest,
    DisposeRequest,
)
from app.dto.approval.approval_response import (
    ApprovalResponse,
    ApprovalListResponse,
    ApprovalListItemResponse,
)

__all__ = [
    "ApprovalRequest",
    "ApprovalListRequest",
    "DisposeRequest",
    "ApprovalResponse",
    "ApprovalListResponse",
    "ApprovalListItemResponse",
]
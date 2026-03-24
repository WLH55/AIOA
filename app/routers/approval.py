"""
审批路由模块

提供审批管理相关的 API 端点
"""
import logging

from fastapi import APIRouter, Depends, status

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.approval_service import ApprovalService
from app.dto.approval.approval_request import ApprovalRequest, ApprovalListRequest, DisposeRequest
from app.dto.approval.approval_response import ApprovalResponse, ApprovalListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approval", tags=["审批管理"])


@router.get(
    "/list",
    response_model=ApiResponse[ApprovalListResponse],
    summary="审批列表",
    description="查询审批列表",
)
async def list_approvals(
    request: ApprovalListRequest = Depends(),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ApprovalListResponse]:
    """
    审批列表接口

    需要携带有效的 Bearer Token
    type=1: 我提交的, type=2: 待我审批的
    """
    response = await ApprovalService.list(request, current_user)
    return ApiResponse.success(data=response)


@router.put(
    "/dispose",
    response_model=ApiResponse[dict],
    summary="处理审批",
    description="处理审批（通过/拒绝/撤销）",
)
async def dispose_approval(
    request: DisposeRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    处理审批接口

    需要携带有效的 Bearer Token
    通过: status=2, 拒绝: status=3, 撤销: status=4
    """
    await ApprovalService.dispose(request, current_user)
    return ApiResponse.success(message="处理审批成功")


@router.get(
    "/{approval_id}",
    response_model=ApiResponse[ApprovalResponse],
    summary="获取审批详情",
    description="根据审批ID获取审批详细信息",
)
async def get_approval_info(
    approval_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ApprovalResponse]:
    """
    获取审批详情接口

    需要携带有效的 Bearer Token
    """
    response = await ApprovalService.info(approval_id)
    return ApiResponse.success(data=response)


@router.post(
    "",
    response_model=ApiResponse[str],
    status_code=status.HTTP_201_CREATED,
    summary="创建审批申请",
    description="创建新的审批申请",
)
async def create_approval(
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[str]:
    """
    创建审批申请接口

    需要携带有效的 Bearer Token
    """
    approval_id = await ApprovalService.create(request, current_user)
    return ApiResponse.success(data=approval_id, message="创建审批成功")

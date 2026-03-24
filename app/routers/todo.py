"""
待办事项路由模块

提供待办事项管理相关的 API 端点
"""
import logging

from fastapi import APIRouter, Depends, status

from app.config.schemas import ApiResponse
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.todo_service import TodoService
from app.dto.todo.todo_request import TodoRequest, TodoListRequest, FinishTodoRequest, TodoRecordRequest
from app.dto.todo.todo_response import TodoInfoResponse, TodoListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/todo", tags=["待办事项"])


@router.get(
    "/list",
    response_model=ApiResponse[TodoListResponse],
    summary="待办列表",
    description="查询当前用户的待办列表，支持分页",
)
async def list_todos(
    request: TodoListRequest = Depends(),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[TodoListResponse]:
    """
    待办列表接口

    需要携带有效的 Bearer Token
    返回当前用户作为执行人的待办列表
    """
    response = await TodoService.list(request, current_user)
    return ApiResponse.success(data=response)


@router.post(
    "/finish",
    response_model=ApiResponse[dict],
    summary="完成待办",
    description="标记待办事项为已完成（只能完成自己的待办）",
)
async def finish_todo(
    request: FinishTodoRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    完成待办接口

    需要携带有效的 Bearer Token
    只能完成自己作为执行人的待办事项
    """
    await TodoService.finish(request, current_user)
    return ApiResponse.success(message="完成待办成功")


@router.post(
    "/record",
    response_model=ApiResponse[dict],
    summary="创建操作记录",
    description="为待办事项创建操作记录",
)
async def create_todo_record(
    request: TodoRecordRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    创建操作记录接口

    需要携带有效的 Bearer Token
    """
    await TodoService.create_record(request, current_user)
    return ApiResponse.success(message="创建操作记录成功")


@router.get(
    "/{todo_id}",
    response_model=ApiResponse[TodoInfoResponse],
    summary="获取待办详情",
    description="根据待办ID获取待办详细信息",
)
async def get_todo_info(
    todo_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[TodoInfoResponse]:
    """
    获取待办详情接口

    需要携带有效的 Bearer Token
    """
    response = await TodoService.info(todo_id)
    return ApiResponse.success(data=response)


@router.post(
    "",
    response_model=ApiResponse[str],
    status_code=status.HTTP_201_CREATED,
    summary="创建待办",
    description="创建新的待办事项",
)
async def create_todo(
    request: TodoRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[str]:
    """
    创建待办接口

    需要携带有效的 Bearer Token
    """
    todo_id = await TodoService.create(request, current_user)
    return ApiResponse.success(data=todo_id, message="创建待办成功")


@router.put(
    "",
    response_model=ApiResponse[dict],
    summary="编辑待办",
    description="编辑待办事项信息",
)
async def edit_todo(
    request: TodoRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    编辑待办接口

    需要携带有效的 Bearer Token
    """
    await TodoService.edit(request)
    return ApiResponse.success(message="编辑待办成功")


@router.delete(
    "/{todo_id}",
    response_model=ApiResponse[dict],
    summary="删除待办",
    description="删除指定待办事项",
)
async def delete_todo(
    todo_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse[dict]:
    """
    删除待办接口

    需要携带有效的 Bearer Token
    注意: 只有创建人可以删除待办
    """
    await TodoService.delete(todo_id, current_user)
    return ApiResponse.success(message="删除待办成功")

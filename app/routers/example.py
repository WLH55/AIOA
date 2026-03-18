"""
示例路由模块

演示路由层职责：只处理参数校验，不处理 try/except
"""
from typing import Annotated
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.config.schemas import ApiResponse, PageResponse
from app.services.example_service import (
    create_item,
    get_item,
    list_items,
    update_item,
    delete_item,
)

router = APIRouter(prefix="/items", tags=["物品管理"])


# ========== 请求模型 ==========
class ItemCreateRequest(BaseModel):
    """创建物品请求"""

    name: str = Field(..., description="物品名称", min_length=1, max_length=100)
    description: str = Field("", description="物品描述")
    price: float = Field(..., description="价格", gt=0)


class ItemUpdateRequest(BaseModel):
    """更新物品请求"""

    name: str | None = Field(None, description="物品名称", min_length=1, max_length=100)
    description: str | None = Field(None, description="物品描述")
    price: float | None = Field(None, description="价格", gt=0)


class ItemResponse(BaseModel):
    """物品响应"""

    id: int
    name: str
    description: str
    price: float


# ========== 路由接口 ==========
@router.post("/", summary="创建物品", response_model=ApiResponse[ItemResponse])
async def create_item_endpoint(request: ItemCreateRequest) -> ApiResponse[ItemResponse]:
    """
    创建物品

    路由层职责：
    - 参数验证（由 Pydantic 自动完成）
    - 调用 Service 层处理业务逻辑
    - 返回统一响应格式

    注意：不在路由层处理 try/except，异常由全局异常处理器处理
    """
    # 直接调用 Service 层，不捕获异常
    item = create_item(request.model_dump())

    return ApiResponse.success(data=item, message="创建成功")


@router.get("/{item_id}", summary="获取物品", response_model=ApiResponse[ItemResponse])
async def get_item_endpoint(item_id: int) -> ApiResponse[ItemResponse]:
    """获取物品详情"""
    # 直接调用 Service 层，不捕获异常
    item = get_item(item_id)

    return ApiResponse.success(data=item)


@router.get("/", summary="获取物品列表", response_model=ApiResponse[PageResponse[ItemResponse]])
async def list_items_endpoint(
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页大小")] = 10,
) -> ApiResponse[PageResponse[ItemResponse]]:
    """获取物品列表（分页）"""
    # 直接调用 Service 层，不捕获异常
    items, total = list_items(page, page_size)

    page_data = PageResponse.create(items, total, page, page_size)

    return ApiResponse.success(data=page_data)


@router.put("/{item_id}", summary="更新物品", response_model=ApiResponse[ItemResponse])
async def update_item_endpoint(
    item_id: int,
    request: ItemUpdateRequest,
) -> ApiResponse[ItemResponse]:
    """更新物品"""
    # 直接调用 Service 层，不捕获异常
    item = update_item(item_id, request.model_dump(exclude_unset=True))

    return ApiResponse.success(data=item, message="更新成功")


@router.delete("/{item_id}", summary="删除物品", response_model=ApiResponse[None])
async def delete_item_endpoint(item_id: int) -> ApiResponse[None]:
    """删除物品"""
    # 直接调用 Service 层，不捕获异常
    delete_item(item_id)

    return ApiResponse.success(message="删除成功")

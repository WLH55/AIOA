"""
示例 Service 模块

演示 Service 层职责：处理业务逻辑和异常捕获
"""
import logging
from typing import Dict, Any, Tuple

from app.config.exceptions import BusinessValidationException, ResourceNotFoundException

logger = logging.getLogger(__name__)


def create_item(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建物品

    Service 层职责：
    - 业务逻辑处理
    - try/except 异常捕获和转换
    - 日志记录
    """
    try:
        # 业务逻辑处理
        if data["price"] <= 0:
            raise BusinessValidationException("价格必须大于 0")

        # 调用数据库或外部 API
        # item = db.insert(data)

        # 模拟返回
        item = {
            "id": 1,
            "name": data["name"],
            "description": data.get("description", ""),
            "price": data["price"]
        }

        logger.info(f"创建物品成功: {item['id']}")
        return item

    except BusinessValidationException:
        raise
    except Exception as e:
        logger.error(f"创建物品失败: {e}")
        raise BusinessValidationException("创建物品失败")


def get_item(item_id: int) -> Dict[str, Any]:
    """获取物品详情"""
    try:
        if item_id <= 0:
            raise ResourceNotFoundException(f"物品 {item_id} 不存在")

        # 调用数据库
        # item = db.query(item_id)

        # 模拟返回
        item = {
            "id": item_id,
            "name": "示例物品",
            "description": "",
            "price": 99.99
        }

        return item

    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"获取物品失败: {e}")
        raise BusinessValidationException("获取物品失败")


def list_items(page: int, page_size: int) -> Tuple[list[Dict[str, Any]], int]:
    """获取物品列表"""
    try:
        # 调用数据库
        # items, total = db.list(page, page_size)

        # 模拟返回
        items = [
            {"id": 1, "name": "物品1", "description": "", "price": 99.99},
            {"id": 2, "name": "物品2", "description": "", "price": 199.99},
        ]
        total = 2

        return items, total

    except Exception as e:
        logger.error(f"获取物品列表失败: {e}")
        raise BusinessValidationException("获取物品列表失败")


def update_item(item_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """更新物品"""
    try:
        if item_id <= 0:
            raise ResourceNotFoundException(f"物品 {item_id} 不存在")

        # 调用数据库
        # item = db.update(item_id, data)

        # 模拟返回
        item = {
            "id": item_id,
            "name": data.get("name", "更新后的物品"),
            "description": data.get("description", ""),
            "price": data.get("price", 99.99)
        }

        logger.info(f"更新物品成功: {item_id}")
        return item

    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"更新物品失败: {e}")
        raise BusinessValidationException("更新物品失败")


def delete_item(item_id: int) -> None:
    """删除物品"""
    try:
        if item_id <= 0:
            raise ResourceNotFoundException(f"物品 {item_id} 不存在")

        # 调用数据库
        # db.delete(item_id)

        logger.info(f"删除物品成功: {item_id}")

    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"删除物品失败: {e}")
        raise BusinessValidationException("删除物品失败")

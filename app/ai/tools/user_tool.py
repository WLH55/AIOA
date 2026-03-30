"""
用户查询工具

提供按用户名查找用户信息的能力
"""
import logging
from typing import List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.repository.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserNameInput(BaseModel):
    """用户名查询输入"""
    name: str = Field(..., description="用户名（中文姓名）")


async def _get_user_by_name(name: str) -> str:
    """
    通过用户名查找用户（异步实现）

    Args:
        name: 用户名

    Returns:
        格式化的用户信息或未找到提示
    """
    user = await UserRepository.find_by_name(name)
    if not user:
        return f"未找到用户：{name}"
    return f"找到用户：{user.name}，用户ID：{str(user.id)}"


def get_user_tool() -> List[StructuredTool]:
    """获取用户查询工具"""
    return [
        StructuredTool.from_function(
            coroutine=_get_user_by_name,
            name="getUserByName",
            description="通过用户名查找用户。当用户提到某个人的名字时，使用此工具将名字转换为用户ID。支持精确匹配用户名。",
            args_schema=UserNameInput,
        )
    ]

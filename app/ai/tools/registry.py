"""
工具注册中心

统一管理 AI Agent 可调用的工具列表，支持按用户上下文动态注入
"""
import logging
from typing import List

from langchain_core.tools import BaseTool

from app.ai.tools.time_tool import get_time_tools
from app.ai.tools.user_tool import get_user_tool
from app.ai.tools.department_tool import get_department_tools
from app.ai.tools.todo_tool import get_todo_tools
from app.ai.tools.approval_tool import get_approval_tools

logger = logging.getLogger(__name__)


def get_all_tools(user_id: str, user_name: str) -> List[BaseTool]:
    """
    获取当前用户可用的全部工具列表

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名

    Returns:
        工具列表
    """
    tools: List[BaseTool] = []
    tools.extend(get_time_tools())
    tools.extend(get_user_tool())
    tools.extend(get_department_tools())
    tools.extend(get_todo_tools(user_id, user_name))
    tools.extend(get_approval_tools(user_id, user_name))
    logger.debug(f"注册工具数量: {len(tools)}, 用户: {user_name}")
    return tools

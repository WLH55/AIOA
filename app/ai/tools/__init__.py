"""
AI 工具模块

导入所有工具模块以触发自动注册
"""
from app.ai.tools.base import ToolProvider
from app.ai.tools.registry import TOOL_REGISTRY, get_all_tools

# 导入所有工具模块（触发自动注册）
from app.ai.tools.time_tool import TimeToolProvider
from app.ai.tools.user_tool import UserToolProvider
from app.ai.tools.todo_tool import TodoToolProvider
from app.ai.tools.approval_tool import ApprovalToolProvider
from app.ai.tools.knowledge_tool import KnowledgeToolProvider


__all__ = [
    "ToolProvider",
    "TOOL_REGISTRY",
    "get_all_tools",
    "TimeToolProvider",
    "UserToolProvider",
    "TodoToolProvider",
    "ApprovalToolProvider",
    "KnowledgeToolProvider",
]
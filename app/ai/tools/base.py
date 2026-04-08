"""
工具提供者基类

定义统一的工具注册接口，各工具模块继承实现后自动注册到全局注册中心
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from langchain_core.tools import BaseTool


class ToolProvider(ABC):
    """
    工具提供者抽象基类

    所有工具模块应继承此基类，实现 get_tools 方法，
    并在模块导入时调用 register() 注册到全局注册中心
    """

    name: str = ""
    description: str = ""
    requires_context: bool = False
    category: str = "general"

    @abstractmethod
    def get_tools(
        self,
        user_id: str = None,
        user_name: str = None,
        context: Dict[str, Any] = None,
    ) -> List[BaseTool]:
        """
        获取工具列表

        Args:
            user_id: 当前用户 ID（requires_context=True 时必须）
            user_name: 当前用户名（requires_context=True 时必须）
            context: 额外上下文信息

        Returns:
            工具列表
        """

    def register(self) -> None:
        """注册到全局工具注册中心"""
        from app.ai.tools.registry import TOOL_REGISTRY
        TOOL_REGISTRY.register(self)

    def __repr__(self) -> str:
        return f"<ToolProvider name={self.name} requires_context={self.requires_context}>"
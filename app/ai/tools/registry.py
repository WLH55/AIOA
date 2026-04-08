"""
工具注册中心

统一管理 AI Agent 可调用的工具列表，支持自动注册和按用户上下文动态注入
"""
import logging
from typing import List, Dict, Any, Optional

from langchain_core.tools import BaseTool

from app.ai.tools.base import ToolProvider

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册中心

    管理所有已注册的 ToolProvider，按需获取工具列表
    """

    def __init__(self):
        self._providers: Dict[str, ToolProvider] = {}

    def register(self, provider: ToolProvider) -> None:
        """
        注册工具提供者

        Args:
            provider: ToolProvider 实例
        """
        if not provider.name:
            logger.warning(f"ToolProvider 缺少 name 属性，跳过注册")
            return
        if provider.name in self._providers:
            logger.warning(f"ToolProvider '{provider.name}' 已注册，将被覆盖")
        self._providers[provider.name] = provider
        logger.debug(f"注册 ToolProvider: {provider.name}")

    def unregister(self, name: str) -> bool:
        """
        取消注册工具提供者

        Args:
            name: 工具模块名称

        Returns:
            是否成功取消
        """
        if name in self._providers:
            del self._providers[name]
            return True
        return False

    def get_provider(self, name: str) -> Optional[ToolProvider]:
        """
        获取指定的工具提供者

        Args:
            name: 工具模块名称

        Returns:
            ToolProvider 实例或 None
        """
        return self._providers.get(name)

    def get_all_providers(self) -> List[ToolProvider]:
        """
        获取所有已注册的工具提供者

        Returns:
            ToolProvider 列表
        """
        return list(self._providers.values())

    def get_all_tools(
        self,
        user_id: str = None,
        user_name: str = None,
        context: Dict[str, Any] = None,
    ) -> List[BaseTool]:
        """
        获取所有工具列表

        Args:
            user_id: 当前用户 ID
            user_name: 当前用户名
            context: 额外上下文信息

        Returns:
            合并后的工具列表
        """
        tools: List[BaseTool] = []
        for provider in self._providers.values():
            if provider.requires_context:
                if not user_id or not user_name:
                    logger.warning(
                        f"ToolProvider '{provider.name}' 需要用户上下文但未提供，跳过"
                    )
                    continue
            provider_tools = provider.get_tools(user_id, user_name, context)
            tools.extend(provider_tools)
        logger.debug(f"获取工具数量: {len(tools)}, 用户: {user_name}")
        return tools

    def get_tools_by_category(self, category: str) -> List[ToolProvider]:
        """
        按类别获取工具提供者

        Args:
            category: 工具类别

        Returns:
            该类别下的 ToolProvider 列表
        """
        return [
            p for p in self._providers.values()
            if p.category == category
        ]


# 全局工具注册中心实例
TOOL_REGISTRY = ToolRegistry()


def get_all_tools(user_id: str, user_name: str) -> List[BaseTool]:
    """
    获取当前用户可用的全部工具列表（兼容旧接口）

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名

    Returns:
        工具列表
    """
    return TOOL_REGISTRY.get_all_tools(user_id, user_name)
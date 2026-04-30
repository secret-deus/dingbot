"""
工具注册模块（ECS MCP）

提供MCP工具的注册、发现和管理功能（只读查询工具）。
"""

import asyncio
from typing import Dict, List, Optional, Type, Any
from abc import ABC, abstractmethod
from loguru import logger

from .mcp_protocol import MCPToolSchema, MCPCallToolResult


class MCPToolBase(ABC):
    """MCP工具基类"""

    def __init__(self, name: str, description: str, timeout: Optional[int] = None, category: Optional[str] = None):
        self.name = name
        self.description = description
        self.timeout = timeout  # 工具级别的超时时间（秒）
        self.category = category or "ecs"
        self.enabled = True
        self.execution_count = 0
        self.last_execution_time = None

        logger.debug(f"工具 {name} 初始化完成，超时: {timeout}秒")

    @abstractmethod
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具"""
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self):
        self.enabled = True
        logger.info(f"工具 {self.name} 已启用")

    def disable(self):
        self.enabled = False
        logger.info(f"工具 {self.name} 已禁用")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time,
        }


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, MCPToolBase] = {}
        self._categories: Dict[str, List[str]] = {}
        logger.info("工具注册表初始化完成")

    def register(self, tool: MCPToolBase, category: str = "ecs") -> bool:
        try:
            if tool.name in self._tools:
                logger.warning(f"工具 {tool.name} 已存在，将替换")

            self._tools[tool.name] = tool

            if category not in self._categories:
                self._categories[category] = []

            if tool.name not in self._categories[category]:
                self._categories[category].append(tool.name)

            logger.info(f"工具 {tool.name} 注册成功，分类: {category}")
            return True
        except Exception as e:
            logger.error(f"注册工具 {tool.name} 失败: {e}")
            return False

    def list_tools(self, category: str = None, enabled_only: bool = True) -> List[MCPToolBase]:
        tools = []
        if category:
            tool_names = self._categories.get(category, [])
            tools = [self._tools[name] for name in tool_names if name in self._tools]
        else:
            tools = list(self._tools.values())

        if enabled_only:
            tools = [t for t in tools if t.is_enabled()]
        return tools

    def get_tool(self, tool_name: str) -> Optional[MCPToolBase]:
        return self._tools.get(tool_name)

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPCallToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return MCPCallToolResult.error(f"工具 {tool_name} 不存在")
        if not tool.is_enabled():
            return MCPCallToolResult.error(f"工具 {tool_name} 已禁用")
        try:
            import time
            start_time = time.time()
            result = await tool.execute(arguments)
            execution_time = time.time() - start_time
            tool.execution_count += 1
            tool.last_execution_time = time.time()
            logger.info(f"工具 {tool_name} 执行完成，耗时: {execution_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行失败: {e}")
            return MCPCallToolResult.error(f"工具执行失败: {str(e)}")

    def clear_category(self, category: str):
        if category not in self._categories:
            return
        for name in list(self._categories[category]):
            self._tools.pop(name, None)
        self._categories[category].clear()


tool_registry = ToolRegistry()


def register_tool(category: str = "ecs"):
    def decorator(cls: Type[MCPToolBase]):
        if not issubclass(cls, MCPToolBase):
            raise TypeError("工具类必须继承自MCPToolBase")
        tool_instance = cls()
        tool_registry.register(tool_instance, category)
        return cls
    return decorator

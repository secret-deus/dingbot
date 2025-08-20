"""
工具注册模块

提供MCP工具的注册、发现和管理功能
"""

import asyncio
from typing import Dict, List, Optional, Type, Any
from abc import ABC, abstractmethod
from loguru import logger

from .mcp_protocol import MCPToolSchema, MCPCallToolResult


class MCPToolBase(ABC):
    """MCP工具基类"""
    
    def __init__(self, name: str, description: str):
        """初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description
        self.enabled = True
        self.execution_count = 0
        self.last_execution_time = None
        
        logger.debug(f"工具 {name} 初始化完成")
    
    @abstractmethod
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具
        
        Args:
            arguments: 工具参数
            
        Returns:
            MCPCallToolResult: 执行结果
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查工具是否启用"""
        return self.enabled
    
    def enable(self):
        """启用工具"""
        self.enabled = True
        logger.info(f"工具 {self.name} 已启用")
    
    def disable(self):
        """禁用工具"""
        self.enabled = False
        logger.info(f"工具 {self.name} 已禁用")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, MCPToolBase] = {}
        self._categories: Dict[str, List[str]] = {}
        logger.info("工具注册表初始化完成")
    
    def register(self, tool: MCPToolBase, category: str = "default") -> bool:
        """注册工具
        
        Args:
            tool: 工具实例
            category: 工具分类
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if tool.name in self._tools:
                logger.warning(f"工具 {tool.name} 已存在，将替换")
            
            self._tools[tool.name] = tool
            
            # 添加到分类
            if category not in self._categories:
                self._categories[category] = []
            
            if tool.name not in self._categories[category]:
                self._categories[category].append(tool.name)
            
            logger.info(f"工具 {tool.name} 注册成功，分类: {category}")
            return True
            
        except Exception as e:
            logger.error(f"注册工具 {tool.name} 失败: {e}")
            return False
    
    def unregister(self, tool_name: str) -> bool:
        """注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if tool_name not in self._tools:
                logger.warning(f"工具 {tool_name} 不存在")
                return False
            
            # 从所有分类中移除
            for category, tools in self._categories.items():
                if tool_name in tools:
                    tools.remove(tool_name)
            
            del self._tools[tool_name]
            logger.info(f"工具 {tool_name} 注销成功")
            return True
            
        except Exception as e:
            logger.error(f"注销工具 {tool_name} 失败: {e}")
            return False
    
    def get_tool(self, tool_name: str) -> Optional[MCPToolBase]:
        """获取工具实例
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[MCPToolBase]: 工具实例
        """
        return self._tools.get(tool_name)
    
    def list_tools(self, category: str = None, enabled_only: bool = True) -> List[MCPToolBase]:
        """列出工具
        
        Args:
            category: 工具分类过滤
            enabled_only: 是否只返回启用的工具
            
        Returns:
            List[MCPToolBase]: 工具列表
        """
        tools = []
        
        if category:
            tool_names = self._categories.get(category, [])
            tools = [self._tools[name] for name in tool_names if name in self._tools]
        else:
            tools = list(self._tools.values())
        
        if enabled_only:
            tools = [tool for tool in tools if tool.is_enabled()]
        
        return tools
    
    def get_tool_schemas(self, category: str = None, enabled_only: bool = True) -> List[MCPToolSchema]:
        """获取工具Schema列表
        
        Args:
            category: 工具分类过滤
            enabled_only: 是否只返回启用的工具
            
        Returns:
            List[MCPToolSchema]: Schema列表
        """
        tools = self.list_tools(category, enabled_only)
        schemas = []
        
        for tool in tools:
            try:
                schema = tool.get_schema()
                schemas.append(schema)
            except Exception as e:
                logger.error(f"获取工具 {tool.name} 的Schema失败: {e}")
        
        return schemas
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._categories.keys())
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """获取指定分类的工具名称列表"""
        return self._categories.get(category, [])
    
    def enable_tool(self, tool_name: str) -> bool:
        """启用工具"""
        tool = self.get_tool(tool_name)
        if tool:
            tool.enable()
            return True
        return False
    
    def disable_tool(self, tool_name: str) -> bool:
        """禁用工具"""
        tool = self.get_tool(tool_name)
        if tool:
            tool.disable()
            return True
        return False
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        stats = {
            "total_tools": len(self._tools),
            "enabled_tools": len([t for t in self._tools.values() if t.is_enabled()]),
            "categories": len(self._categories),
            "tools": []
        }
        
        for tool in self._tools.values():
            stats["tools"].append(tool.get_stats())
        
        return stats
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            MCPCallToolResult: 执行结果
        """
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
    
    def clear(self):
        """清空所有工具"""
        self._tools.clear()
        self._categories.clear()
        logger.info("工具注册表已清空")
    
    def validate_tool_name(self, tool_name: str) -> bool:
        """验证工具名称格式"""
        if not tool_name or not isinstance(tool_name, str):
            return False
        
        # 工具名称应该只包含字母、数字、连字符和下划线
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        return re.match(pattern, tool_name) is not None
    
    def bulk_register(self, tools: List[MCPToolBase], category: str = "default") -> Dict[str, bool]:
        """批量注册工具
        
        Args:
            tools: 工具列表
            category: 工具分类
            
        Returns:
            Dict[str, bool]: 注册结果
        """
        results = {}
        
        for tool in tools:
            results[tool.name] = self.register(tool, category)
        
        return results
    
    def search_tools(self, query: str, category: str = None) -> List[MCPToolBase]:
        """搜索工具
        
        Args:
            query: 搜索查询
            category: 工具分类过滤
            
        Returns:
            List[MCPToolBase]: 匹配的工具列表
        """
        tools = self.list_tools(category, enabled_only=False)
        matching_tools = []
        
        query_lower = query.lower()
        
        for tool in tools:
            # 在工具名称和描述中搜索
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                matching_tools.append(tool)
        
        return matching_tools


# 全局工具注册表实例
tool_registry = ToolRegistry()


def register_tool(category: str = "default"):
    """工具注册装饰器
    
    Args:
        category: 工具分类
    """
    def decorator(cls: Type[MCPToolBase]):
        if not issubclass(cls, MCPToolBase):
            raise TypeError("工具类必须继承自MCPToolBase")
        
        # 创建工具实例并注册
        tool_instance = cls()
        tool_registry.register(tool_instance, category)
        
        return cls
    
    return decorator


def get_available_tools(category: str = None) -> List[MCPToolBase]:
    """获取可用工具列表
    
    Args:
        category: 工具分类过滤
        
    Returns:
        List[MCPToolBase]: 可用工具列表
    """
    return tool_registry.list_tools(category, enabled_only=True)


def get_tool_by_name(tool_name: str) -> Optional[MCPToolBase]:
    """根据名称获取工具
    
    Args:
        tool_name: 工具名称
        
    Returns:
        Optional[MCPToolBase]: 工具实例
    """
    return tool_registry.get_tool(tool_name)


def execute_tool_by_name(tool_name: str, arguments: Dict[str, Any]) -> MCPCallToolResult:
    """根据名称执行工具
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        MCPCallToolResult: 执行结果
    """
    return asyncio.run(tool_registry.execute_tool(tool_name, arguments)) 
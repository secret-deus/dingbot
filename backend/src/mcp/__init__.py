"""
MCP 包初始化
- 确保子模块可通过属性访问（兼容 unittest.mock.patch('mcp.config_manager....')）
"""

from importlib import import_module as _import_module

# 暴露子模块为属性，便于测试中的patch路径解析
config_manager = _import_module('.config_manager', __name__)
config = _import_module('.config', __name__)
enhanced_client = _import_module('.enhanced_client', __name__)
types = _import_module('.types', __name__)

# 常用类便捷导出（非必须）
try:
    from .config_manager import MCPConfigManager  # noqa: F401
    from .config import MCPConfiguration  # noqa: F401
except Exception:
    # 避免在导入阶段由于依赖问题导致失败
    pass



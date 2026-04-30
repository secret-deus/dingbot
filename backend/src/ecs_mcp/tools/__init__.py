"""
ECS MCP 工具集
"""

from ..core.tool_registry import tool_registry


# 安全的只读查询工具列表（初始仅包含监控查询工具）
SAFE_QUERY_TOOLS = []


def register_all_tools():
    from loguru import logger

    # 延迟导入工具以避免循环
    # 每次注册前清空列表，避免重复追加导致重复注册
    global SAFE_QUERY_TOOLS
    SAFE_QUERY_TOOLS = []
    try:
        from .ecs_monitor_data import EcsDescribeInstanceMonitorDataTool
        SAFE_QUERY_TOOLS.append(EcsDescribeInstanceMonitorDataTool)
    except Exception as e:
        logger.error(f"导入ECS工具失败: {e}")
    try:
        from .ecs_list_instances import EcsListInstancesTool
        SAFE_QUERY_TOOLS.append(EcsListInstancesTool)
    except Exception as e:
        logger.error(f"导入ECS工具失败: {e}")
    try:
        from .ecs_inspection import EcsInspectionTool
        SAFE_QUERY_TOOLS.append(EcsInspectionTool)
    except Exception as e:
        logger.error(f"导入ECS工具失败: {e}")

    success_count = 0
    for tool_cls in SAFE_QUERY_TOOLS:
        try:
            tool_instance = tool_cls()
            if tool_registry.register(tool_instance, "ecs"):
                success_count += 1
                logger.info(f"✅ 工具 {tool_instance.name} 注册成功")
        except Exception as e:
            logger.error(f"注册工具失败 {tool_cls.__name__}: {e}")

    logger.info(f"🎯 成功注册 {success_count}/{len(SAFE_QUERY_TOOLS)} 个ECS工具")
    return success_count

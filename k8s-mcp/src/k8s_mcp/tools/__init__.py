"""
K8s MCP工具模块

包含各种Kubernetes操作工具的实现
"""

from .k8s_get_pods import K8sGetPodsTool
from .k8s_get_services import K8sGetServicesTool
from .k8s_get_deployments import K8sGetDeploymentsTool
from .k8s_get_nodes import K8sGetNodesTool
from .k8s_scale_deployment import K8sScaleDeploymentTool
from .k8s_get_logs import K8sGetLogsTool
from .k8s_describe_pod import K8sDescribePodTool
from .k8s_get_events import K8sGetEventsTool

# 新增的Deployment管理工具
from .k8s_restart_deployment import K8sRestartDeploymentTool
from .k8s_rollback_deployment import K8sRollbackDeploymentTool
from .k8s_get_deployment_history import K8sGetDeploymentHistoryTool
from .k8s_patch_deployment import K8sPatchDeploymentTool

# 新增的Service网络管理工具
from .k8s_create_service import K8sCreateServiceTool
from .k8s_update_service import K8sUpdateServiceTool
from .k8s_get_endpoints import K8sGetEndpointsTool
from .k8s_patch_service import K8sPatchServiceTool

# 新增的Deployment创建工具
from .k8s_generate_deployment_yaml import K8sGenerateDeploymentYamlTool
from .k8s_create_deployment import K8sCreateDeploymentTool
from .k8s_llm_generate_deployment import K8sLLMGenerateDeploymentTool

# 智能查询工具
from .k8s_relation_query import K8sRelationQueryTool
from .k8s_cluster_summary import K8sClusterSummaryTool

from ..core.tool_registry import tool_registry

# 可用工具列表
# 安全的查询工具列表 - 只包含读取操作，不包含修改集群的危险操作
SAFE_QUERY_TOOLS = [
    # 基础查询工具
    K8sGetPodsTool,
    K8sGetServicesTool,
    K8sGetDeploymentsTool,
    K8sGetNodesTool,
    K8sGetLogsTool,
    K8sDescribePodTool,
    K8sGetEventsTool,
    
    # 历史和端点查询
    K8sGetDeploymentHistoryTool,
    K8sGetEndpointsTool,
    
    # 智能查询工具
    K8sRelationQueryTool,
    K8sClusterSummaryTool,
]

# 危险的修改工具列表 - 这些工具会修改集群状态，已被禁用
DANGEROUS_MODIFICATION_TOOLS = [
    # K8sScaleDeploymentTool,           # 扩缩容 - 危险操作
    # K8sRestartDeploymentTool,         # 重启 - 危险操作
    # K8sRollbackDeploymentTool,        # 回滚 - 危险操作
    # K8sPatchDeploymentTool,           # 修改配置 - 危险操作
    # K8sCreateServiceTool,             # 创建服务 - 危险操作
    # K8sUpdateServiceTool,             # 更新服务 - 危险操作
    # K8sPatchServiceTool,              # 修改服务 - 危险操作
    # K8sGenerateDeploymentYamlTool,    # 生成配置 - 可能误导
    # K8sCreateDeploymentTool,          # 创建部署 - 危险操作
    # K8sLLMGenerateDeploymentTool,     # LLM生成部署 - 危险操作
]

# 当前启用的工具列表 - 只包含安全的查询工具
AVAILABLE_TOOLS = SAFE_QUERY_TOOLS


def register_all_tools():
    """注册所有安全的查询工具"""
    from loguru import logger
    
    success_count = 0
    total_safe_tools = len(SAFE_QUERY_TOOLS)
    total_dangerous_tools = len(DANGEROUS_MODIFICATION_TOOLS)
    
    logger.info(f"🔒 安全模式启用: 只注册 {total_safe_tools} 个安全查询工具")
    logger.info(f"🚫 已禁用 {total_dangerous_tools} 个危险修改工具")
    
    for tool_class in AVAILABLE_TOOLS:  # AVAILABLE_TOOLS 现在只包含 SAFE_QUERY_TOOLS
        try:
            tool_instance = tool_class()
            result = tool_registry.register(tool_instance, "kubernetes")
            if result:
                success_count += 1
                logger.info(f"✅ 安全工具 {tool_instance.name} 注册成功")
            else:
                logger.error(f"❌ 工具 {tool_instance.name} 注册失败")
        except Exception as e:
            logger.error(f"❌ 注册工具 {tool_class.__name__} 时发生错误: {e}")
    
    logger.info(f"🎯 安全模式: 成功注册 {success_count}/{len(AVAILABLE_TOOLS)} 个K8s查询工具")
    
    if success_count < len(AVAILABLE_TOOLS):
        logger.warning(f"⚠️ 有 {len(AVAILABLE_TOOLS) - success_count} 个工具注册失败")
    
    return success_count


def get_available_tools():
    """获取可用工具列表"""
    return tool_registry.list_tools("kubernetes", enabled_only=True)


__all__ = [
    # 安全的查询工具 - 只包含读取操作
    "K8sGetPodsTool", "K8sGetServicesTool", "K8sGetDeploymentsTool",
    "K8sGetNodesTool", "K8sGetLogsTool", "K8sDescribePodTool", 
    "K8sGetEventsTool", "K8sGetDeploymentHistoryTool", "K8sGetEndpointsTool",
    
    # 智能查询工具
    "K8sRelationQueryTool", "K8sClusterSummaryTool",
    
    # 工具列表
    "SAFE_QUERY_TOOLS", "DANGEROUS_MODIFICATION_TOOLS", "AVAILABLE_TOOLS",
    
    # 函数
    "register_all_tools", "get_available_tools"
] 
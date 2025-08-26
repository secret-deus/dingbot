"""
任务执行引擎实现
复用现有的MCP客户端和LLM处理器，支持集群巡检、资源分析等任务类型
集成现有的数据脱敏机制，确保数据安全
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from loguru import logger

from .models import ScheduledTask, TaskExecution, TaskStatus, TaskType
from ..mcp.enhanced_client import EnhancedMCPClient
from ..llm.processor import EnhancedLLMProcessor
from ..mcp.types import ChatMessage


class TaskExecutor:
    """
    任务执行引擎
    负责执行不同类型的定时任务，复用现有的MCP和LLM集成
    """
    
    def __init__(self, mcp_client: EnhancedMCPClient, llm_processor: EnhancedLLMProcessor):
        """
        初始化任务执行引擎
        
        Args:
            mcp_client: MCP客户端实例
            llm_processor: LLM处理器实例
        """
        self.mcp_client = mcp_client
        self.llm_processor = llm_processor
        
        # 执行统计
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "execution_times": []
        }
        
        logger.info("✅ TaskExecutor初始化完成")
    
    async def execute_task(self, task: ScheduledTask, execution: TaskExecution) -> Dict[str, Any]:
        """
        执行任务的主入口方法
        
        Args:
            task: 任务配置
            execution: 执行记录
            
        Returns:
            执行结果字典
        """
        logger.info(f"🚀 开始执行任务: {task.name} (类型: {task.task_type.value})")
        
        start_time = datetime.now()
        
        try:
            # 更新执行状态
            execution.status = TaskStatus.RUNNING
            execution.started_at = start_time
            
            # 根据任务类型执行相应逻辑
            if task.task_type == TaskType.CLUSTER_CHECK:
                result = await self._execute_cluster_check(task, execution)
            elif task.task_type == TaskType.RESOURCE_ANALYSIS:
                result = await self._execute_resource_analysis(task, execution)
            elif task.task_type == TaskType.HEALTH_MONITOR:
                result = await self._execute_health_monitor(task, execution)
            elif task.task_type == TaskType.CUSTOM:
                result = await self._execute_custom_task(task, execution)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")
            
            # 更新执行统计
            self.execution_stats["total_executions"] += 1
            self.execution_stats["successful_executions"] += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.execution_stats["execution_times"].append(execution_time)
            
            # 保留最近100次执行时间
            if len(self.execution_stats["execution_times"]) > 100:
                self.execution_stats["execution_times"] = self.execution_stats["execution_times"][-100:]
            
            logger.info(f"✅ 任务执行成功: {task.name}, 耗时: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            
            logger.error(f"❌ 任务执行失败: {task.name}, 错误: {e}")
            raise
    
    async def _execute_cluster_check(self, task: ScheduledTask, execution: TaskExecution) -> Dict[str, Any]:
        """
        执行集群巡检任务
        复用现有的perform_inspection逻辑
        """
        try:
            # 导入现有的巡检功能
            from ..api.v2.endpoints.inspection import perform_inspection, InspectionScope, InspectionOptions
            
            # 构建巡检参数
            config = task.config or {}
            scope_config = config.get("scope", {})
            analysis_config = config.get("analysis", {})
            
            scope = InspectionScope(
                namespace=scope_config.get("namespace"),
                includeNamespaces=scope_config.get("namespaces"),
                maxDepth=scope_config.get("max_depth", 2)
            )
            
            options = InspectionOptions(
                sendToDingTalk=False,  # 由调度器统一处理通知
                summaryType=analysis_config.get("summary_type", "overview"),
                includeAnomalies=analysis_config.get("include_anomalies", True),
                maxSizeKB=analysis_config.get("max_size_kb", 16),
                llmModel=analysis_config.get("llm_model")
            )
            
            # 执行巡检 (复用现有函数)
            result = await perform_inspection(
                mcp_client=self.mcp_client,
                llm_processor=self.llm_processor,
                scope=scope,
                options=options,
                dingtalk_enabled=False  # 由调度器处理通知
            )
            
            # 包装结果
            return {
                "type": "cluster_check",
                "task_type": "cluster_check",
                "analysis_id": result.get("analysisId"),
                "analysis_markdown": result.get("analysisMarkdown"),
                "tool_payload": result.get("toolPayload"),
                "summary": self._extract_summary_from_markdown(result.get("analysisMarkdown", "")),
                "timestamp": datetime.now().isoformat(),
                "execution_id": execution.id
            }
            
        except Exception as e:
            logger.error(f"集群巡检执行失败: {e}")
            raise
    
    async def _execute_resource_analysis(self, task: ScheduledTask, execution: TaskExecution) -> Dict[str, Any]:
        """
        执行资源利用率分析任务
        调用Prometheus资源分析工具
        """
        try:
            # 构建分析参数
            config = task.config or {}
            tool_params = {
                "prometheus_url": config.get("prometheus_url", ""),
                "days": config.get("days", 14),
                "cpu_threshold": config.get("cpu_threshold", 60.0),
                "memory_threshold": config.get("memory_threshold", 60.0),
                "analysis_mode": config.get("analysis_mode", "deployment"),
                "namespace_filter": config.get("namespace_filter", "")
            }
            
            # 如果配置了使用环境变量，则不传递prometheus_url
            if config.get("use_env_config", False):
                tool_params.pop("prometheus_url", None)
            
            logger.info(f"调用Prometheus资源分析工具，参数: {tool_params}")
            
            # 调用MCP工具
            analysis_result = await self.mcp_client.call_tool("k8s-prometheus-resource-analysis", tool_params)
            
            # 使用LLM生成分析报告
            llm_analysis = await self._generate_resource_analysis_report(analysis_result, config)
            
            return {
                "type": "resource_analysis",
                "task_type": "resource_analysis",
                "analysis_result": analysis_result,
                "llm_analysis": llm_analysis,
                "parameters": tool_params,
                "summary": self._extract_resource_analysis_summary(analysis_result),
                "timestamp": datetime.now().isoformat(),
                "execution_id": execution.id
            }
            
        except Exception as e:
            logger.error(f"资源分析执行失败: {e}")
            raise
    
    async def _execute_health_monitor(self, task: ScheduledTask, execution: TaskExecution) -> Dict[str, Any]:
        """
        执行健康监控任务
        """
        try:
            # 构建监控参数
            config = task.config or {}
            
            health_results = {}
            health_issues = []
            
            # 检查服务状态
            if config.get("check_services", True):
                logger.info("检查服务状态...")
                services = await self.mcp_client.call_tool("k8s-get-services", {
                    "namespace": config.get("namespace", "")
                })
                health_results["services"] = services
                
                # 分析服务健康状态
                service_issues = self._analyze_service_health(services)
                health_issues.extend(service_issues)
            
            # 检查部署状态
            if config.get("check_deployments", True):
                logger.info("检查部署状态...")
                deployments = await self.mcp_client.call_tool("k8s-get-deployments", {
                    "namespace": config.get("namespace", "")
                })
                health_results["deployments"] = deployments
                
                # 分析部署健康状态
                deployment_issues = self._analyze_deployment_health(deployments)
                health_issues.extend(deployment_issues)
            
            # 检查Pod状态
            if config.get("check_pods", True):
                logger.info("检查Pod状态...")
                pods = await self.mcp_client.call_tool("k8s-get-pods", {
                    "namespace": config.get("namespace", "")
                })
                health_results["pods"] = pods
                
                # 分析Pod健康状态
                pod_issues = self._analyze_pod_health(pods)
                health_issues.extend(pod_issues)
            
            # 检查节点状态
            if config.get("check_nodes", True):
                logger.info("检查节点状态...")
                nodes = await self.mcp_client.call_tool("k8s-get-nodes", {})
                health_results["nodes"] = nodes
                
                # 分析节点健康状态
                node_issues = self._analyze_node_health(nodes)
                health_issues.extend(node_issues)
            
            # 生成健康监控报告
            health_report = await self._generate_health_monitor_report(health_results, health_issues, config)
            
            return {
                "type": "health_monitor",
                "task_type": "health_monitor",
                "health_results": health_results,
                "health_issues": health_issues,
                "health_report": health_report,
                "summary": f"发现 {len(health_issues)} 个健康问题",
                "timestamp": datetime.now().isoformat(),
                "execution_id": execution.id
            }
            
        except Exception as e:
            logger.error(f"健康监控执行失败: {e}")
            raise
    
    async def _execute_custom_task(self, task: ScheduledTask, execution: TaskExecution) -> Dict[str, Any]:
        """
        执行自定义任务
        """
        try:
            config = task.config or {}
            
            # 自定义任务可以包含多个MCP工具调用
            tool_calls = config.get("tool_calls", [])
            results = {}
            
            for i, tool_call in enumerate(tool_calls):
                tool_name = tool_call.get("tool_name")
                tool_params = tool_call.get("parameters", {})
                
                if not tool_name:
                    continue
                
                logger.info(f"执行自定义工具调用 {i+1}: {tool_name}")
                
                try:
                    result = await self.mcp_client.call_tool(tool_name, tool_params)
                    results[f"tool_{i+1}_{tool_name}"] = result
                except Exception as e:
                    logger.error(f"自定义工具调用失败 {tool_name}: {e}")
                    results[f"tool_{i+1}_{tool_name}"] = {"error": str(e)}
            
            # 如果配置了LLM分析，则生成分析报告
            llm_analysis = None
            if config.get("enable_llm_analysis", False):
                llm_analysis = await self._generate_custom_task_report(results, config)
            
            return {
                "type": "custom",
                "task_type": "custom",
                "tool_results": results,
                "llm_analysis": llm_analysis,
                "summary": f"执行了 {len(tool_calls)} 个工具调用",
                "timestamp": datetime.now().isoformat(),
                "execution_id": execution.id
            }
            
        except Exception as e:
            logger.error(f"自定义任务执行失败: {e}")
            raise
    
    async def _generate_resource_analysis_report(self, analysis_result: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        使用LLM生成资源分析报告
        """
        try:
            system_prompt = (
                "你是资深的Kubernetes运维专家，请基于Prometheus资源利用率分析数据，"
                "生成专业的资源优化报告：\n"
                "- 总体资源利用率概况\n"
                "- 资源利用率过低的应用列表\n"
                "- 具体的资源优化建议\n"
                "- 预期的资源节省效果\n"
                "- 实施建议和注意事项\n"
                "请使用Markdown格式，内容要专业且可操作。"
            )
            
            json_text = json.dumps(analysis_result, ensure_ascii=False, default=str)
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(
                    role="user",
                    content=f"请分析以下Prometheus资源利用率数据：\n{json_text[:15000]}"
                )
            ]
            
            # 使用LLM生成分析报告
            result = await self.llm_processor._chat_without_tools(messages)
            return result.content or "LLM分析报告生成失败"
            
        except Exception as e:
            logger.error(f"生成资源分析报告失败: {e}")
            return f"资源分析报告生成失败: {str(e)}"
    
    async def _generate_health_monitor_report(self, health_results: Dict[str, Any], 
                                            health_issues: List[Dict[str, Any]], 
                                            config: Dict[str, Any]) -> str:
        """
        使用LLM生成健康监控报告
        """
        try:
            system_prompt = (
                "你是资深的Kubernetes运维专家，请基于集群健康监控数据，"
                "生成专业的健康状态报告：\n"
                "- 集群整体健康状态评估\n"
                "- 发现的问题详细分析\n"
                "- 问题的严重程度分级\n"
                "- 具体的修复建议\n"
                "- 预防措施和最佳实践\n"
                "请使用Markdown格式，突出重要问题。"
            )
            
            # 构建分析数据
            analysis_data = {
                "health_results": health_results,
                "health_issues": health_issues,
                "issue_count": len(health_issues)
            }
            
            json_text = json.dumps(analysis_data, ensure_ascii=False, default=str)
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(
                    role="user",
                    content=f"请分析以下集群健康监控数据：\n{json_text[:15000]}"
                )
            ]
            
            # 使用LLM生成分析报告
            result = await self.llm_processor._chat_without_tools(messages)
            return result.content or "LLM健康监控报告生成失败"
            
        except Exception as e:
            logger.error(f"生成健康监控报告失败: {e}")
            return f"健康监控报告生成失败: {str(e)}"
    
    async def _generate_custom_task_report(self, tool_results: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        使用LLM生成自定义任务报告
        """
        try:
            system_prompt = config.get("llm_prompt", 
                "你是资深的运维专家，请基于以下工具执行结果，生成专业的分析报告。"
                "请使用Markdown格式，提供清晰的分析和建议。"
            )
            
            json_text = json.dumps(tool_results, ensure_ascii=False, default=str)
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(
                    role="user",
                    content=f"请分析以下工具执行结果：\n{json_text[:15000]}"
                )
            ]
            
            # 使用LLM生成分析报告
            result = await self.llm_processor._chat_without_tools(messages)
            return result.content or "LLM自定义任务报告生成失败"
            
        except Exception as e:
            logger.error(f"生成自定义任务报告失败: {e}")
            return f"自定义任务报告生成失败: {str(e)}"
    
    def _extract_summary_from_markdown(self, markdown_text: str) -> str:
        """
        从Markdown文本中智能提取巡检摘要
        """
        try:
            if not markdown_text:
                return "集群巡检已完成"
            
            lines = markdown_text.split('\n')
            summary_parts = []
            
            # 提取关键信息
            cluster_info = {}
            anomalies = []
            resource_stats = {}
            
            for line in lines:
                line = line.strip()
                
                # 提取集群基本信息
                if "节点数量" in line or "Node数量" in line:
                    cluster_info["nodes"] = self._extract_number_from_line(line)
                elif "Pod总数" in line or "Pod数量" in line:
                    cluster_info["pods"] = self._extract_number_from_line(line)
                elif "Service数量" in line:
                    cluster_info["services"] = self._extract_number_from_line(line)
                elif "Deployment数量" in line:
                    cluster_info["deployments"] = self._extract_number_from_line(line)
                
                # 提取异常信息
                elif "异常" in line or "错误" in line or "失败" in line or "Pending" in line or "CrashLoopBackOff" in line:
                    if not line.startswith('#') and len(line) > 10:
                        anomalies.append(line)
                
                # 提取资源使用情况
                elif "CPU使用率" in line or "内存使用率" in line:
                    resource_stats["usage"] = line
                elif "资源不足" in line or "资源紧张" in line:
                    resource_stats["issues"] = line
            
            # 构建摘要
            if cluster_info:
                parts = []
                if cluster_info.get("nodes"):
                    parts.append(f"节点{cluster_info['nodes']}个")
                if cluster_info.get("pods"):
                    parts.append(f"Pod{cluster_info['pods']}个")
                if cluster_info.get("services"):
                    parts.append(f"Service{cluster_info['services']}个")
                
                if parts:
                    summary_parts.append(f"集群规模: {', '.join(parts)}")
            
            # 添加异常信息
            if anomalies:
                anomaly_count = len(anomalies)
                if anomaly_count <= 2:
                    summary_parts.append(f"发现异常: {'; '.join(anomalies[:2])}")
                else:
                    summary_parts.append(f"发现{anomaly_count}个异常，包括: {anomalies[0]}")
            else:
                summary_parts.append("集群状态正常")
            
            # 添加资源信息
            if resource_stats.get("usage"):
                summary_parts.append(resource_stats["usage"])
            elif resource_stats.get("issues"):
                summary_parts.append(resource_stats["issues"])
            
            # 如果没有提取到有用信息，使用简单摘要
            if not summary_parts:
                # 尝试提取前几行有意义的内容
                meaningful_lines = []
                for line in lines[:15]:
                    line = line.strip()
                    if (line and not line.startswith('#') and not line.startswith('---') 
                        and len(line) > 10 and not line.startswith('生成时间')):
                        meaningful_lines.append(line)
                        if len(meaningful_lines) >= 2:
                            break
                
                if meaningful_lines:
                    summary_parts = meaningful_lines
                else:
                    summary_parts = ["集群巡检已完成"]
            
            # 限制长度并返回
            summary = '; '.join(summary_parts)
            return summary[:300] if len(summary) > 300 else summary
            
        except Exception as e:
            logger.error(f"提取巡检摘要失败: {e}")
            return "集群巡检已完成"
    
    def _extract_number_from_line(self, line: str) -> str:
        """
        从文本行中提取数字
        """
        import re
        numbers = re.findall(r'\d+', line)
        return numbers[0] if numbers else ""
    
    def _extract_resource_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """
        从资源分析结果中提取摘要
        """
        try:
            if isinstance(analysis_result, dict):
                # 提取关键信息
                total_apps = analysis_result.get("total_applications", 0)
                underutilized_apps = analysis_result.get("underutilized_applications", 0)
                
                if total_apps > 0:
                    return f"分析了 {total_apps} 个应用，发现 {underutilized_apps} 个资源利用率过低的应用"
                else:
                    return "资源利用率分析已完成"
            else:
                return "资源利用率分析已完成"
                
        except Exception:
            return "资源利用率分析已完成"
    
    def _analyze_service_health(self, services: Any) -> List[Dict[str, Any]]:
        """
        分析服务健康状态
        """
        issues = []
        
        try:
            if isinstance(services, dict) and "items" in services:
                for service in services["items"]:
                    service_name = service.get("metadata", {}).get("name", "unknown")
                    
                    # 检查服务是否有端点
                    spec = service.get("spec", {})
                    if spec.get("type") == "ClusterIP" and not spec.get("clusterIP"):
                        issues.append({
                            "type": "service",
                            "name": service_name,
                            "severity": "warning",
                            "issue": "服务没有分配ClusterIP",
                            "description": f"服务 {service_name} 没有有效的ClusterIP"
                        })
                        
        except Exception as e:
            logger.error(f"分析服务健康状态失败: {e}")
        
        return issues
    
    def _analyze_deployment_health(self, deployments: Any) -> List[Dict[str, Any]]:
        """
        分析部署健康状态
        """
        issues = []
        
        try:
            if isinstance(deployments, dict) and "items" in deployments:
                for deployment in deployments["items"]:
                    deployment_name = deployment.get("metadata", {}).get("name", "unknown")
                    status = deployment.get("status", {})
                    
                    # 检查副本数
                    replicas = status.get("replicas", 0)
                    ready_replicas = status.get("readyReplicas", 0)
                    
                    if replicas > 0 and ready_replicas < replicas:
                        issues.append({
                            "type": "deployment",
                            "name": deployment_name,
                            "severity": "error",
                            "issue": "部分副本未就绪",
                            "description": f"部署 {deployment_name} 有 {replicas} 个副本，但只有 {ready_replicas} 个就绪"
                        })
                        
        except Exception as e:
            logger.error(f"分析部署健康状态失败: {e}")
        
        return issues
    
    def _analyze_pod_health(self, pods: Any) -> List[Dict[str, Any]]:
        """
        分析Pod健康状态
        """
        issues = []
        
        try:
            if isinstance(pods, dict) and "items" in pods:
                for pod in pods["items"]:
                    pod_name = pod.get("metadata", {}).get("name", "unknown")
                    status = pod.get("status", {})
                    
                    # 检查Pod状态
                    phase = status.get("phase", "")
                    if phase not in ["Running", "Succeeded"]:
                        issues.append({
                            "type": "pod",
                            "name": pod_name,
                            "severity": "error" if phase == "Failed" else "warning",
                            "issue": f"Pod状态异常: {phase}",
                            "description": f"Pod {pod_name} 状态为 {phase}"
                        })
                    
                    # 检查容器状态
                    container_statuses = status.get("containerStatuses", [])
                    for container_status in container_statuses:
                        if not container_status.get("ready", False):
                            container_name = container_status.get("name", "unknown")
                            issues.append({
                                "type": "container",
                                "name": f"{pod_name}/{container_name}",
                                "severity": "warning",
                                "issue": "容器未就绪",
                                "description": f"Pod {pod_name} 中的容器 {container_name} 未就绪"
                            })
                            
        except Exception as e:
            logger.error(f"分析Pod健康状态失败: {e}")
        
        return issues
    
    def _analyze_node_health(self, nodes: Any) -> List[Dict[str, Any]]:
        """
        分析节点健康状态
        """
        issues = []
        
        try:
            if isinstance(nodes, dict) and "items" in nodes:
                for node in nodes["items"]:
                    node_name = node.get("metadata", {}).get("name", "unknown")
                    status = node.get("status", {})
                    
                    # 检查节点条件
                    conditions = status.get("conditions", [])
                    for condition in conditions:
                        condition_type = condition.get("type", "")
                        condition_status = condition.get("status", "")
                        
                        if condition_type == "Ready" and condition_status != "True":
                            issues.append({
                                "type": "node",
                                "name": node_name,
                                "severity": "error",
                                "issue": "节点未就绪",
                                "description": f"节点 {node_name} 状态为 NotReady"
                            })
                        elif condition_type in ["MemoryPressure", "DiskPressure", "PIDPressure"] and condition_status == "True":
                            issues.append({
                                "type": "node",
                                "name": node_name,
                                "severity": "warning",
                                "issue": f"节点资源压力: {condition_type}",
                                "description": f"节点 {node_name} 存在 {condition_type} 压力"
                            })
                            
        except Exception as e:
            logger.error(f"分析节点健康状态失败: {e}")
        
        return issues
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        获取执行统计信息
        """
        total = self.execution_stats["total_executions"]
        successful = self.execution_stats["successful_executions"]
        failed = self.execution_stats["failed_executions"]
        execution_times = self.execution_stats["execution_times"]
        
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_execution_time": avg_time,
            "recent_execution_times": execution_times[-10:] if execution_times else []
        }
    
    def reset_stats(self):
        """
        重置执行统计
        """
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "execution_times": []
        }
        logger.info("执行统计已重置")


# 全局执行器实例
_executor_instance: Optional[TaskExecutor] = None


def get_task_executor() -> Optional[TaskExecutor]:
    """获取全局执行器实例"""
    return _executor_instance


def initialize_task_executor(mcp_client: EnhancedMCPClient, llm_processor: EnhancedLLMProcessor) -> TaskExecutor:
    """初始化全局执行器"""
    global _executor_instance
    
    if _executor_instance is None:
        _executor_instance = TaskExecutor(mcp_client, llm_processor)
    
    return _executor_instance


def cleanup_task_executor():
    """清理全局执行器"""
    global _executor_instance
    _executor_instance = None

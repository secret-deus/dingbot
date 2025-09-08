"""
K8s资源管理API端点
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
import asyncio

from ....mcp.enhanced_client import EnhancedMCPClient

# 获取MCP客户端的依赖函数
def get_mcp_client():
    """获取MCP客户端实例"""
    try:
        from main import mcp_client
        return mcp_client
    except ImportError:
        return None


router = APIRouter(prefix="/resources", tags=["K8s资源管理"])


def _summarize_update_result(result_text: str) -> dict:
    """
    摘要资源更新结果，只保留异常资源的详细信息
    
    Args:
        result_text: MCP工具返回的完整结果文本
        
    Returns:
        dict: 包含摘要信息的字典
    """
    import re
    
    # 调试：记录输入文本
    with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
        f.write(f"🔍 _summarize_update_result 开始处理:\n")
        f.write(f"输入文本长度: {len(result_text)}\n")
        f.write(f"输入文本前1000字符:\n{result_text[:1000]}\n")
        f.write("=" * 50 + "\n")
    
    # 提取统计数字
    total_apps = 0
    successful_updates = 0
    failed_updates = 0
    
    # 匹配统计信息 - 更宽松的正则表达式，支持前缀符号
    total_match = re.search(r'[-*]?\s*总应用数[:：]\s*(\d+)', result_text)
    if total_match:
        total_apps = int(total_match.group(1))
    
    success_match = re.search(r'[-*]?\s*成功更新[:：]\s*(\d+)', result_text)
    if success_match:
        successful_updates = int(success_match.group(1))
    
    failed_match = re.search(r'[-*]?\s*更新失败[:：]\s*(\d+)', result_text)
    if failed_match:
        failed_updates = int(failed_match.group(1))
    
    # 调试：记录正则匹配结果
    with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
        f.write(f"🔍 正则匹配结果:\n")
        f.write(f"total_match: {total_match.group(1) if total_match else 'None'}\n")
        f.write(f"success_match: {success_match.group(1) if success_match else 'None'}\n")
        f.write(f"failed_match: {failed_match.group(1) if failed_match else 'None'}\n")
        f.write(f"解析后数值: total_apps={total_apps}, successful_updates={successful_updates}, failed_updates={failed_updates}\n")
        f.write("=" * 50 + "\n")
    
    # 提取失败资源的详细信息
    failed_resources = []
    
    # 查找失败资源的详细信息（通常在"失败详情"或"错误"部分）
    failed_sections = re.findall(
        r'(?:失败详情|错误详情|更新失败)[:：]\s*([^\n]*(?:\n(?!\s*\d+\.|\s*总|\s*成功|\s*失败|\s*##)[^\n]*)*)', 
        result_text, 
        re.MULTILINE
    )
    
    for section in failed_sections:
        if section.strip():
            failed_resources.append(section.strip())
    
    # 如果没有找到结构化的失败信息，尝试提取包含"失败"或"错误"的行
    if not failed_resources and failed_updates > 0:
        failed_lines = re.findall(r'.*(?:失败|错误|Error|Failed).*', result_text, re.IGNORECASE)
        failed_resources = failed_lines[:10]  # 最多保留10条错误信息
    
    # 生成摘要
    summary_lines = [
        f"📊 更新统计: 总计 {total_apps} 个应用",
        f"✅ 成功更新: {successful_updates} 个",
        f"❌ 更新失败: {failed_updates} 个"
    ]
    
    if successful_updates > 0:
        success_rate = (successful_updates / total_apps * 100) if total_apps > 0 else 0
        summary_lines.append(f"📈 成功率: {success_rate:.1f}%")
    
    if failed_updates > 0:
        summary_lines.append("⚠️ 失败资源详情见下方")
    else:
        summary_lines.append("🎉 所有资源更新成功！")
    
    return {
        "total_apps": total_apps,
        "successful_updates": successful_updates,
        "failed_updates": failed_updates,
        "summary": "\n".join(summary_lines),
        "failed_resources": failed_resources[:20]  # 最多保留20个失败资源的详情
    }


class ResourceUpdateRequest(BaseModel):
    """资源更新请求"""
    namespace_filter: Optional[str] = ""
    app_name_filter: Optional[str] = ""
    days: Optional[int] = 14
    max_concurrent: Optional[int] = 5
    force_update: Optional[bool] = False
    time_period: Optional[str] = "14d"  # 新增时间周期参数：14d 或 1d


class ResourceUpdateResponse(BaseModel):
    """资源更新响应"""
    success: bool
    message: str
    total_apps: int
    successful_updates: int
    failed_updates: int
    processing_time_seconds: float
    details: Optional[Dict[str, Any]] = None


class MetricsCoverageResponse(BaseModel):
    """指标覆盖情况响应"""
    success: bool
    total_deployments: int
    with_metrics: int
    without_metrics: int
    outdated_metrics: int
    coverage_rate: float
    aggregator_status: Dict[str, Any]
    report: str


@router.post("/update-metrics", response_model=ResourceUpdateResponse)
async def update_resource_metrics(
    request: ResourceUpdateRequest,
    mcp_client: EnhancedMCPClient = Depends(get_mcp_client)
):
    """
    触发资源指标更新
    
    通过调用MCP工具批量更新知识图谱中的资源利用率指标
    """
    start_time = datetime.now()
    
    # API调用入口日志
    with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
        f.write(f"\n=== API调用开始 ===\n时间: {start_time}\n请求参数: {request}\n=================\n")
    
    # 全局异常捕获
    try:
        # 根据时间周期选择不同的处理方式
        is_day_mode = request.time_period == "1d"
        
        # 调用MCP工具进行批量更新
        tool_params = {
            "namespace_filter": request.namespace_filter,
            "app_name_filter": request.app_name_filter,
            "days": request.days,
            "max_concurrent": request.max_concurrent,
            "time_period": request.time_period  # 传递时间周期参数
        }
        
        # 调用知识图谱指标更新工具（MCP客户端内部已设置10分钟超时）
        result = await mcp_client.call_tool(
            "k8s-update-knowledge-graph-metrics", 
            tool_params
        )
        
        # 调试：记录原始结果结构
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(f"🔍 收到MCP工具原始结果:\n")
            f.write(f"结果类型: {type(result)}\n")
            f.write(f"结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}\n")
            f.write(f"is_error: {result.get('is_error', 'N/A') if isinstance(result, dict) else 'N/A'}\n")
            f.write(f"原始结果: {str(result)[:500]}...\n")
            f.write("=" * 50 + "\n")
        
        if not result or result.get("is_error", False):
            error_msg = "MCP工具调用失败"
            if result and result.get("content"):
                error_msg = result["content"][0].get("text", error_msg)
            
            raise HTTPException(
                status_code=500,
                detail=f"资源指标更新失败: {error_msg}"
            )
        
        # 解析结果
        content = result.get("content", [])
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(f"📋 解析content字段:\n")
            f.write(f"content类型: {type(content)}\n")
            f.write(f"content长度: {len(content) if content else 0}\n")
            if content:
                f.write(f"第一个content项: {str(content[0])[:200]}...\n")
            f.write("=" * 50 + "\n")
            
        if not content:
            raise HTTPException(
                status_code=500,
                detail="MCP工具返回空结果"
            )
        
        result_text = content[0].get("text", "")
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(f"📝 提取result_text:\n")
            f.write(f"text长度: {len(result_text)}\n")
            f.write(f"text前500字符: {result_text[:500]}\n")
            f.write("=" * 50 + "\n")
        
        # 解析和摘要结果
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(f"📊 开始提取摘要:\n")

        # logger.info(f"🔄 开始解析和摘要结果，文本长度: {len(result_text)}")
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(f"🔄 开始解析和摘要结果，文本长度: {len(result_text)}\n")
        
        try:
            summary_result = _summarize_update_result(result_text)
            
            with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
                f.write(f"📊 摘要结果:\n")
                f.write(f"summary_result: {summary_result}\n")
                f.write("=" * 50 + "\n")
                
        except Exception as summary_error:
            # logger.error(f"💥 摘要处理失败: {summary_error}")
            with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
                f.write(f"💥 摘要处理失败: {summary_error}\n")
                f.write(f"💥 摘要处理异常: {summary_error}\n")
                f.write("=" * 50 + "\n")
            raise
        
        total_apps = summary_result["total_apps"]
        successful_updates = summary_result["successful_updates"] 
        failed_updates = summary_result["failed_updates"]
        
        # 调试日志 - 写入文件
        debug_info = f"""
=== 资源更新结果解析 ===
时间: {datetime.now()}
总应用: {total_apps}
成功更新: {successful_updates}
失败更新: {failed_updates}
结果文本前500字符:
{result_text[:500]}
========================
"""
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(debug_info)
        
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 如果更新成功且有异常资源，触发资源分析报告
        analysis_report = None
        
        # 调试日志 - 分析步骤
        analysis_debug = f"""
=== 分析步骤检查 ===
时间: {datetime.now()}
successful_updates: {successful_updates}
条件检查: successful_updates > 0 = {successful_updates > 0}
========================
"""
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(analysis_debug)
        
        if successful_updates > 0:
            try:
                logger.info("🔍 触发资源分析报告...")
                with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"开始调用分析工具: {datetime.now()}\n")
                
                analysis_result = await mcp_client.call_tool(
                    "k8s-resource-analysis-report",
                    {
                        "namespace_filter": request.namespace_filter or "",
                        "include_recommendations": True,
                        "send_dingtalk_notification": True
                    }
                )
                
                if analysis_result and not analysis_result.get("is_error", False):
                    analysis_content = analysis_result.get("content", [])
                    if analysis_content:
                        analysis_report = analysis_content[0].get("text", "")
                        logger.info("✅ 资源分析报告生成完成")
                else:
                    logger.warning("资源分析报告生成失败或返回错误")
                    
            except Exception as e:
                logger.error(f"触发资源分析报告失败: {e}")
        
        return ResourceUpdateResponse(
            success=True,
            message="资源指标更新完成",
            total_apps=total_apps,
            successful_updates=successful_updates,
            failed_updates=failed_updates,
            processing_time_seconds=processing_time,
            details={
                "summary": summary_result["summary"],
                "failed_resources": summary_result["failed_resources"],
                "parameters": tool_params,
                "full_result_available": len(result_text) > 5000,  # 标记是否有完整结果
                "analysis_report": analysis_report  # 添加分析报告
            }
        )
        
    except Exception as global_error:
        # 全局异常捕获，记录所有未处理的异常
        with open("/tmp/resource_debug.log", "a", encoding="utf-8") as f:
            f.write(f"🚨 全局异常捕获: {type(global_error).__name__}: {global_error}\n")
            f.write(f"异常发生时间: {datetime.now()}\n")
            import traceback
            f.write(f"异常堆栈:\n{traceback.format_exc()}\n")
            f.write("=" * 50 + "\n")
        
        # 重新抛出原来的异常处理逻辑
        if isinstance(global_error, asyncio.TimeoutError):
            processing_time = (datetime.now() - start_time).total_seconds()
            raise HTTPException(
                status_code=408,
                detail=f"资源指标更新超时: 处理时间超过10分钟 (实际用时: {processing_time:.1f}秒)"
            )
        elif isinstance(global_error, HTTPException):
            raise global_error
        else:
            processing_time = (datetime.now() - start_time).total_seconds()
            raise HTTPException(
                status_code=500,
                detail=f"资源指标更新失败: {str(global_error)}"
            )



@router.get("/metrics-coverage", response_model=MetricsCoverageResponse)
async def get_metrics_coverage(
    include_details: bool = False,
    filter_namespace: str = "",
    show_failed_only: bool = False,
    mcp_client: EnhancedMCPClient = Depends(get_mcp_client)
):
    """
    获取资源指标覆盖情况报告
    
    显示deployment指标覆盖统计和聚合器状态
    """
    try:
        # 调用指标覆盖报告工具
        tool_params = {
            "include_details": include_details,
            "filter_namespace": filter_namespace,
            "show_failed_only": show_failed_only
        }
        
        result = await mcp_client.call_tool(
            "k8s-metrics-coverage-report",
            tool_params
        )
        
        if not result or result.get("is_error", False):
            error_msg = "MCP工具调用失败"
            if result and result.get("content"):
                error_msg = result["content"][0].get("text", error_msg)
            
            raise HTTPException(
                status_code=500,
                detail=f"获取指标覆盖报告失败: {error_msg}"
            )
        
        # 解析结果
        content = result.get("content", [])
        if not content:
            raise HTTPException(
                status_code=500,
                detail="MCP工具返回空结果"
            )
        
        report_text = content[0].get("text", "")
        
        # 简单解析报告文本获取关键数字
        import re
        
        total_deployments = 0
        with_metrics = 0
        without_metrics = 0
        outdated_metrics = 0
        coverage_rate = 0.0
        
        # 解析统计数字
        total_match = re.search(r'总Deployment数.*?(\d+)', report_text)
        if total_match:
            total_deployments = int(total_match.group(1))
        
        with_match = re.search(r'有指标数据.*?(\d+)', report_text)
        if with_match:
            with_metrics = int(with_match.group(1))
        
        without_match = re.search(r'缺少指标.*?(\d+)', report_text)
        if without_match:
            without_metrics = int(without_match.group(1))
        
        outdated_match = re.search(r'指标过期.*?(\d+)', report_text)
        if outdated_match:
            outdated_metrics = int(outdated_match.group(1))
        
        coverage_match = re.search(r'整体覆盖率.*?([\d.]+)%', report_text)
        if coverage_match:
            coverage_rate = float(coverage_match.group(1))
        
        # 提取聚合器状态
        aggregator_status = {}
        if "运行中" in report_text:
            aggregator_status["is_running"] = True
        elif "未运行" in report_text:
            aggregator_status["is_running"] = False
        
        return MetricsCoverageResponse(
            success=True,
            total_deployments=total_deployments,
            with_metrics=with_metrics,
            without_metrics=without_metrics,
            outdated_metrics=outdated_metrics,
            coverage_rate=coverage_rate,
            aggregator_status=aggregator_status,
            report=report_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取指标覆盖报告失败: {str(e)}"
        )


@router.post("/force-aggregation")
async def force_metrics_aggregation(
    mcp_client: EnhancedMCPClient = Depends(get_mcp_client)
):
    """
    强制触发指标聚合
    
    立即执行一次完整的指标聚合过程
    """
    try:
        # 这里需要调用聚合器的强制聚合方法
        # 由于聚合器在MCP服务器中，我们可能需要通过MCP工具来触发
        
        # 先尝试调用资源监控工具来触发更新
        result = await mcp_client.call_tool(
            "k8s-resource-monitor",
            {
                "action": "force-aggregation"
            }
        )
        
        if result and not result.get("is_error", False):
            content = result.get("content", [])
            message = content[0].get("text", "强制聚合已触发") if content else "强制聚合已触发"
            
            return {
                "success": True,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 如果没有专门的强制聚合工具，返回提示
            return {
                "success": False,
                "message": "强制聚合功能暂不可用，请使用资源指标更新功能",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"强制聚合失败: {str(e)}"
        )

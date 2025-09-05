"""
HTTP API客户端

用于MCP服务器与后端API服务的通信
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


class HttpApiClient:
    """HTTP API客户端类"""
    
    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3):
        """初始化HTTP客户端
        
        Args:
            base_url: 后端API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        
        # 统计信息
        self.stats = {
            "requests_sent": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "last_request_time": None,
            "last_error": None
        }
        
        logger.info(f"HttpApiClient初始化完成，目标API: {self.base_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
        return self.session
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("HttpApiClient会话已关闭")
    
    async def post_with_retry(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """带重试的POST请求
        
        Args:
            endpoint: API端点路径
            data: 请求数据
            
        Returns:
            Optional[Dict[str, Any]]: 响应数据或None（失败时）
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                self.stats["requests_sent"] += 1
                self.stats["last_request_time"] = datetime.now().isoformat()
                
                session = await self._get_session()
                
                logger.debug(f"发送POST请求到 {url} (尝试 {attempt + 1}/{self.max_retries + 1})")
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.stats["requests_success"] += 1
                        logger.info(f"API请求成功: {endpoint}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.warning(f"API请求返回错误状态 {response.status}: {error_text}")
                        
                        if response.status < 500 and attempt == 0:
                            # 4xx错误通常不需要重试
                            break
                            
            except asyncio.TimeoutError:
                logger.warning(f"API请求超时: {url} (尝试 {attempt + 1})")
            except aiohttp.ClientError as e:
                logger.warning(f"API请求客户端错误: {e} (尝试 {attempt + 1})")
            except Exception as e:
                logger.error(f"API请求发生未知错误: {e} (尝试 {attempt + 1})")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries:
                wait_time = (attempt + 1) * 2  # 递增等待时间
                logger.debug(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
        
        # 所有重试都失败了
        self.stats["requests_failed"] += 1
        self.stats["last_error"] = f"请求失败，已重试 {self.max_retries} 次"
        logger.error(f"API请求最终失败: {endpoint}")
        return None
    
    async def send_resource_alert(self, resource_id: str, metrics_data: Dict[str, Any], 
                                 additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """发送资源告警到后端
        
        Args:
            resource_id: 资源ID
            metrics_data: 指标数据
            additional_data: 附加数据
            
        Returns:
            bool: 发送是否成功
        """
        payload = {
            "resource_id": resource_id,
            "metrics": metrics_data,
            "timestamp": datetime.now().isoformat(),
            "source": "k8s-mcp-server"
        }
        
        if additional_data:
            payload.update(additional_data)
        
        try:
            result = await self.post_with_retry("/api/v2/alerts/resource", payload)
            return result is not None
        except Exception as e:
            logger.error(f"发送资源告警失败: {e}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 后端API是否健康
        """
        try:
            result = await self.post_with_retry("/health", {})
            return result is not None
        except Exception as e:
            logger.warning(f"后端API健康检查失败: {e}")
            return False
    
    async def post_alert(self, alert_data: Dict[str, Any]) -> bool:
        """发送告警数据到后端
        
        Args:
            alert_data: 告警数据
            
        Returns:
            bool: 发送是否成功
        """
        try:
            logger.info(f"发送告警数据到后端: {alert_data.get('alert_type', 'unknown')}")
            
            # 发送到告警API端点
            result = await self.post_with_retry("/api/v2/alerts/resource", alert_data)
            
            if result:
                logger.info("✅ 告警数据发送成功")
                return True
            else:
                logger.error("❌ 告警数据发送失败")
                return False
                
        except Exception as e:
            logger.error(f"发送告警数据时发生异常: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取客户端统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "stats": self.stats.copy()
        }


# 全局HTTP客户端实例
_global_http_client: Optional[HttpApiClient] = None


def get_global_http_client(base_url: Optional[str] = None) -> Optional[HttpApiClient]:
    """获取全局HTTP客户端实例
    
    Args:
        base_url: 后端API基础URL，如果提供则创建新实例
        
    Returns:
        Optional[HttpApiClient]: HTTP客户端实例或None
    """
    global _global_http_client
    
    if base_url and (_global_http_client is None or _global_http_client.base_url != base_url):
        _global_http_client = HttpApiClient(base_url)
        logger.info(f"创建新的全局HTTP客户端: {base_url}")
    
    return _global_http_client


async def close_global_http_client():
    """关闭全局HTTP客户端"""
    global _global_http_client
    if _global_http_client:
        await _global_http_client.close()
        _global_http_client = None
        logger.info("全局HTTP客户端已关闭")

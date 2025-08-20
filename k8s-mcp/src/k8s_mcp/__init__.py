"""
Kubernetes MCP服务器

为钉钉K8s运维机器人提供真实的Kubernetes操作支持
"""

__version__ = "1.0.0"
__author__ = "K8s MCP Team"
__email__ = "admin@example.com"

from .server import K8sMCPServer
from .k8s_client import K8sClient
from .config import K8sConfig

__all__ = ["K8sMCPServer", "K8sClient", "K8sConfig"] 
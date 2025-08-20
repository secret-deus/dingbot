#!/usr/bin/env python3
"""
启动K8s MCP HTTP服务器

使用SSE (Server-Sent Events) 协议替代WebSocket
"""

import asyncio
import signal
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from k8s_mcp.server import K8sMCPServer
from k8s_mcp.config import get_config


async def main():
    """主函数"""
    config = get_config()
    
    # 创建服务器实例
    server = K8sMCPServer(config)
    
    # 设置信号处理器
    def signal_handler(signum, frame):
        print(f"\n接收到信号 {signum}，正在关闭服务器...")
        if hasattr(server, 'stop'):
            asyncio.create_task(server.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动服务器
        await server.start()
    except Exception as e:
        print(f"启动服务器失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
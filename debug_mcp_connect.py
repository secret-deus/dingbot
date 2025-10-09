#!/usr/bin/env python3
"""Debug MCP连接问题"""
import asyncio
import sys
sys.path.insert(0, 'backend')

from src.mcp.config_manager import MCPConfigManager, get_mcp_config_manager
from src.mcp.enhanced_client import EnhancedMCPClient, MCPServerConnection
from src.mcp.types import MCPException
from loguru import logger

async def debug_connect():
    """调试连接过程"""
    
    # 1. 加载配置
    logger.info("=" * 60)
    logger.info("步骤1: 加载配置")
    config_mgr = MCPConfigManager('config/mcp_config.json')
    enabled_servers = config_mgr.get_enabled_servers()
    logger.info(f"找到 {len(enabled_servers)} 个启用的服务器:")
    for srv in enabled_servers:
        logger.info(f"  - {srv.name}: type={srv.type}, host={srv.host}, port={srv.port}")
    
    # 2. 创建连接
    logger.info("=" * 60)
    logger.info("步骤2: 创建并测试单个连接")
    if enabled_servers:
        test_server = enabled_servers[0]  # 测试第一个服务器
        logger.info(f"测试连接到: {test_server.name}")
        
        conn = MCPServerConnection(test_server)
        conn.set_config_manager(config_mgr)
        
        try:
            result = await conn.connect()
            logger.info(f"连接结果: {result}")
            logger.info(f"连接状态: {conn.status}")
            logger.info(f"发现的工具数量: {len(conn.tools)}")
            if conn.tools:
                logger.info("工具列表:")
                for tool_name in list(conn.tools.keys())[:5]:
                    logger.info(f"  - {tool_name}")
        except Exception as e:
            logger.error(f"连接失败: {e}", exc_info=True)
    
    # 3. 测试完整的客户端连接
    logger.info("=" * 60)
    logger.info("步骤3: 测试EnhancedMCPClient完整连接流程")
    client = EnhancedMCPClient(config_mgr)
    try:
        await client.connect()
        logger.info(f"客户端连接成功，总工具数: {len(client.tools)}")
    except Exception as e:
        logger.error(f"客户端连接失败: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(debug_connect())


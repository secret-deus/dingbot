"""
MCP stdio 子进程连接与工具发现（从 enhanced_client 拆分，主客户端以 SSE 为热路径）。
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from loguru import logger

from .types import MCPTool, MCPException


async def stdio_connect(connection: Any) -> None:
    """启动 stdio MCP 子进程并挂到 connection.process。"""
    cfg = connection.config
    cmd = [cfg.command]
    if cfg.args:
        cmd.extend(cfg.args)

    env = None
    if cfg.env:
        env = os.environ.copy()
        env.update(cfg.env)

    connection.process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cfg.cwd,
        env=env,
    )

    await asyncio.sleep(1)

    if connection.process.returncode is not None:
        raise MCPException(
            "STDIO_FAILED",
            f"stdio子进程启动失败: {connection.process.returncode}",
        )

    logger.info(f"stdio MCP服务器启动成功: {cmd[0]}")


async def stdio_discover_tools(connection: Any) -> None:
    """通过 stdio JSON-RPC 发现工具并写入 connection.tools。"""
    if not connection.process:
        raise MCPException("STDIO_NOT_CONNECTED", "stdio进程未连接")

    list_tools_message = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1,
    }

    message_json = json.dumps(list_tools_message) + "\n"
    connection.process.stdin.write(message_json.encode())
    await connection.process.stdin.drain()

    response_line = await connection.process.stdout.readline()
    if not response_line:
        raise MCPException("STDIO_NO_RESPONSE", "stdio进程无响应")

    response_data = json.loads(response_line.decode().strip())

    if "error" in response_data:
        raise MCPException(
            "TOOL_DISCOVERY_FAILED",
            f"工具发现失败: {response_data['error']}",
        )

    tools_data = response_data.get("result", {}).get("tools", [])
    for tool_data in tools_data:
        tool = MCPTool(
            name=tool_data["name"],
            description=tool_data.get("description", ""),
            input_schema=tool_data.get("inputSchema", {}),
            timeout=tool_data.get("timeout"),
            category=tool_data.get("category"),
            version=tool_data.get("version"),
            provider=connection.config.name,
        )
        connection.tools[tool.name] = tool

    logger.info(f"stdio发现 {len(connection.tools)} 个工具")

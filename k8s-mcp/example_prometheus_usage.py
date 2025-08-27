#!/usr/bin/env python3
"""
Prometheus应用资源分析工具使用示例

展示如何通过MCP服务器调用k8s-prometheus-app-metrics工具
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime


async def call_prometheus_tool_via_mcp():
    """通过MCP服务器调用Prometheus工具"""
    
    # MCP服务器地址
    mcp_server_url = "http://localhost:8080"  # 根据实际配置调整
    
    # 工具调用请求
    tool_request = {
        "id": f"req_{int(datetime.now().timestamp())}",
        "name": "k8s-prometheus-app-metrics",
        "arguments": {
            "app_name": "nginx",
            "namespace": "default",
            "days": 7
        }
    }
    
    print(f"🚀 调用Prometheus应用资源分析工具...")
    print(f"📋 请求参数: {json.dumps(tool_request, indent=2, ensure_ascii=False)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 调用工具
            async with session.post(
                f"{mcp_server_url}/tools/call",
                json=tool_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 调用成功!")
                    print(f"📊 响应状态: {result.get('status', 'unknown')}")
                    print(f"💬 响应消息: {result.get('message', 'no message')}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 调用失败: HTTP {response.status}")
                    print(f"错误详情: {error_text}")
                    
    except Exception as e:
        print(f"❌ 请求异常: {e}")


async def monitor_sse_events():
    """监听MCP服务器的SSE事件流"""
    
    mcp_server_url = "http://localhost:8080"
    
    print(f"🔊 开始监听MCP服务器事件流...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{mcp_server_url}/events") as response:
                if response.status == 200:
                    print("✅ 成功连接到事件流")
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith('event:'):
                            event_type = line_str[6:].strip()
                            print(f"📡 事件类型: {event_type}")
                            
                        elif line_str.startswith('data:'):
                            try:
                                data_str = line_str[5:].strip()
                                data = json.loads(data_str)
                                
                                if event_type == 'tool_complete':
                                    print(f"🎉 工具执行完成: {data.get('tool', 'unknown')}")
                                    print(f"⏱️  执行时间: {data.get('execution_time', 0):.2f}秒")
                                    
                                elif event_type == 'tool_error':
                                    print(f"❌ 工具执行错误: {data.get('tool', 'unknown')}")
                                    print(f"🔍 错误信息: {data.get('error', 'unknown error')}")
                                    
                            except json.JSONDecodeError:
                                pass
                                
                else:
                    print(f"❌ 连接事件流失败: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ 监听异常: {e}")


async def main():
    """主函数"""
    
    print("🔧 Prometheus应用资源分析工具使用示例")
    print("=" * 50)
    
    # 检查环境配置
    print("\n📋 检查环境配置...")
    
    prometheus_url = os.getenv("PROMETHEUS_URL")
    if prometheus_url:
        print(f"✅ Prometheus URL: {prometheus_url}")
    else:
        print("⚠️  未配置PROMETHEUS_URL环境变量")
    
    auth_type = os.getenv("PROMETHEUS_AUTH_TYPE", "none")
    print(f"🔐 认证类型: {auth_type}")
    
    # 选择操作模式
    print("\n🎯 选择操作模式:")
    print("1. 直接调用工具")
    print("2. 监听事件流")
    print("3. 两者都执行")
    
    choice = input("请选择 (1/2/3): ").strip()
    
    if choice == "1":
        await call_prometheus_tool_via_mcp()
    elif choice == "2":
        await monitor_sse_events()
    elif choice == "3":
        # 并发执行
        await asyncio.gather(
            call_prometheus_tool_via_mcp(),
            monitor_sse_events()
        )
    else:
        print("❌ 无效选择")
    
    print("\n✅ 示例执行完成!")


if __name__ == "__main__":
    # 设置示例环境变量（可选）
    # os.environ["PROMETHEUS_URL"] = "http://your-prometheus-server:9090"
    # os.environ["PROMETHEUS_ACCESS_KEY"] = "your-access-key"
    # os.environ["PROMETHEUS_SECRET_KEY"] = "your-secret-key"
    # os.environ["PROMETHEUS_AUTH_TYPE"] = "basic"
    
    asyncio.run(main())

#!/usr/bin/env python3
"""
K8s MCP服务器简化启动脚本

这个脚本提供了一个简单的启动入口，自动检测Poetry环境
可以通过以下方式运行：
- python run.py
- poetry run python run.py
- ./run.py
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    project_root = Path(__file__).parent
    
    print("🚀 K8s MCP服务器启动中...")
    print(f"📁 项目目录: {project_root}")
    
    # 检查是否在Poetry虚拟环境中
    virtual_env = os.environ.get("VIRTUAL_ENV")
    
    if virtual_env:
        print(f"🎯 检测到虚拟环境: {Path(virtual_env).name}")
        # 直接运行启动脚本
        os.chdir(project_root)
        subprocess.run([sys.executable, "start_k8s_mcp_server.py"])
    else:
        # 检查是否有Poetry
        try:
            result = subprocess.run(
                ["poetry", "--version"], 
                capture_output=True, 
                text=True, 
                cwd=project_root
            )
            
            if result.returncode == 0:
                print(f"🎯 检测到Poetry: {result.stdout.strip()}")
                print("🔧 使用Poetry环境启动服务器...")
                os.chdir(project_root)
                subprocess.run(["poetry", "run", "python", "start_k8s_mcp_server.py"])
            else:
                print("❌ Poetry未安装或配置错误")
                sys.exit(1)
                
        except FileNotFoundError:
            print("❌ Poetry未安装")
            print("请先安装Poetry:")
            print("  curl -sSL https://install.python-poetry.org | python3 -")
            print("  或者: pip install poetry")
            sys.exit(1)

if __name__ == "__main__":
    main() 
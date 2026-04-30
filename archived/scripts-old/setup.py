#!/usr/bin/env python3
"""
项目初始化脚本
安装前端依赖并进行基础设置
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并输出结果"""
    print(f"🔧 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 命令失败: {cmd}")
        print(f"错误输出: {result.stderr}")
        return False
    else:
        print(f"✅ 命令成功: {cmd}")
        if result.stdout:
            print(result.stdout)
        return True

def main():
    """主函数"""
    print("🚀 开始项目初始化...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    backend_dir = project_root / "backend"
    
    print(f"📁 项目根目录: {project_root}")
    
    # 1. 检查Node.js是否安装
    if not run_command("node --version"):
        print("❌ Node.js未安装，请先安装Node.js")
        sys.exit(1)
    
    if not run_command("npm --version"):
        print("❌ npm未安装，请先安装npm")
        sys.exit(1)
    
    # 2. 安装前端依赖
    print("\n📦 安装前端依赖...")
    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        sys.exit(1)
    
    if not run_command("npm install", cwd=frontend_dir):
        print("❌ 前端依赖安装失败")
        sys.exit(1)
    
    # 3. 创建必要的目录
    print("\n📁 创建必要目录...")
    directories = [
        backend_dir / "logs",
        backend_dir / "static"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")
    
    # 4. 检查后端配置
    print("\n⚙️  检查后端配置...")
    config_file = backend_dir / "config.env"
    if not config_file.exists():
        example_file = backend_dir / "config.env.example"
        if example_file.exists():
            print(f"📋 复制配置示例: {config_file}")
            run_command(f"cp {example_file} {config_file}")
        else:
            print("⚠️  配置文件不存在，将使用默认配置")
    
    print("\n🎉 项目初始化完成！")
    print("\n📖 下一步:")
    print("1. 开发环境: poetry run dev")
    print("2. 构建项目: poetry run build")
    print("3. 启动服务: poetry run serve")

if __name__ == "__main__":
    main() 
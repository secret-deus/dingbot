#!/usr/bin/env python3
"""
生产环境服务脚本
启动集成的前后端服务（单端口）
"""

import os
import subprocess
import sys
from pathlib import Path

def check_build():
    """检查构建文件是否存在"""
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    static_dir = backend_dir / "static"
    
    # 检查关键文件
    key_files = [
        static_dir / "index.html",
        static_dir / "spa" / "index.html"
    ]
    
    missing_files = []
    for file_path in key_files:
        if not file_path.exists():
            missing_files.append(str(file_path.relative_to(project_root)))
    
    if missing_files:
        print("❌ 缺少构建文件:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 请先运行构建命令:")
        print("   poetry run build")
        return False
    
    return True

def run_production():
    """直接启动生产服务（用于Poetry脚本）"""
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    env['ENV'] = 'production'
    
    # 启动服务（简化版，适合Poetry脚本）
    cmd = [
        "uvicorn", 
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    try:
        subprocess.run(cmd, cwd=backend_dir, env=env, check=True)
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("🚀 启动生产环境服务...")
    
    # 检查构建文件
    if not check_build():
        sys.exit(1)
    
    # 获取项目目录
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    env['ENV'] = 'production'
    
    print("📁 项目根目录:", project_root)
    print("🔧 工作目录:", backend_dir)
    print("🌍 环境:", env.get('ENV', 'development'))
    
    # 启动服务
    cmd = [
        "uvicorn", 
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--workers", "1",
        "--access-log"
    ]
    
    print(f"🚀 执行命令: {' '.join(cmd)}")
    print("=" * 50)
    print("🎉 服务启动中...")
    print("📖 访问地址:")
    print("   主页: http://localhost:8000")
    print("   SPA应用: http://localhost:8000/spa/")
    print("   API文档: http://localhost:8000/docs")
    print("   系统状态: http://localhost:8000/api/status")
    print("=" * 50)
    print("💡 按 Ctrl+C 停止服务")
    print()
    
    try:
        # 启动uvicorn服务
        subprocess.run(cmd, cwd=backend_dir, env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 收到停止信号，正在关闭服务...")
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
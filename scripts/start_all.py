#!/usr/bin/env python3
"""
集成启动脚本
先启动 MCP 服务器，再启动后端服务器
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from typing import List, Optional

# 项目根目录
project_root = Path(__file__).parent.parent


def log_output(process: subprocess.Popen, prefix: str):
    """在后台线程中输出进程日志"""
    def _log():
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"[{prefix}] {line.rstrip()}")
        except Exception:
            pass
    thread = threading.Thread(target=_log, daemon=True)
    thread.start()
    return thread


class ProcessManager:
    """进程管理器"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
    def add_process(self, process: subprocess.Popen, log_prefix: Optional[str] = None):
        """添加进程到管理器"""
        self.processes.append(process)
        if log_prefix and process.stdout:
            log_output(process, log_prefix)
        
    def wait_for_port(self, host: str, port: int, timeout: int = 30) -> bool:
        """等待端口可用"""
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False
        
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}，正在关闭所有服务...")
        self.running = False
        self.stop_all()
        sys.exit(0)
        
    def stop_all(self):
        """停止所有进程"""
        for process in self.processes:
            try:
                if process.poll() is None:  # 进程仍在运行
                    print(f"正在停止进程 PID {process.pid}...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                print(f"停止进程时出错: {e}")


def start_ecs_mcp(manager: ProcessManager) -> bool:
    """启动 ECS MCP 服务器"""
    print("🚀 启动 ECS MCP 服务器...")
    
    ecs_mcp_dir = project_root / "ecs-mcp"
    if not ecs_mcp_dir.exists():
        print("⚠️  ECS MCP 目录不存在，跳过启动")
        return True  # 不是错误，只是跳过
    
    # 检查 poetry 环境
    try:
        result = subprocess.run(
            ["poetry", "env", "info", "--path"],
            cwd=ecs_mcp_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("⚠️  ECS MCP Poetry 环境未配置，尝试安装依赖...")
            subprocess.run(["poetry", "install"], cwd=ecs_mcp_dir, timeout=60)
    except Exception as e:
        print(f"⚠️  检查 ECS MCP 环境时出错: {e}")
        
    # 检查端口配置
    ecs_port = int(os.getenv("ECS_MCP_PORT", "8002"))
    
    # 启动 ECS MCP
    env = os.environ.copy()
    # 禁用 reload 模式，避免环境问题
    env['ECS_MCP_RELOAD'] = 'false'
    # 设置 PYTHONPATH，确保能找到 ecs_mcp 模块
    src_path = str(ecs_mcp_dir / "src")
    existing_pythonpath = env.get('PYTHONPATH', '')
    if existing_pythonpath:
        env['PYTHONPATH'] = f"{src_path}{os.pathsep}{existing_pythonpath}"
    else:
        env['PYTHONPATH'] = src_path
    
    try:
        # 获取 poetry 环境的 Python 解释器
        result = subprocess.run(
            ["poetry", "env", "info", "-p"],
            cwd=str(ecs_mcp_dir.absolute()),
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            venv_path = Path(result.stdout.strip())
            
            # 使用 poetry 环境的 uvicorn 直接启动，禁用 reload
            uvicorn_exe = venv_path / "bin" / "uvicorn"
            if not uvicorn_exe.exists():
                uvicorn_exe = venv_path / "Scripts" / "uvicorn.exe"  # Windows
            
            # 从环境变量获取端口，默认 8002
            host = os.getenv("ECS_MCP_HOST", "0.0.0.0")
            port = os.getenv("ECS_MCP_PORT", "8002")
            
            process = subprocess.Popen(
                [str(uvicorn_exe), "ecs_mcp.server:app",
                 "--host", host,
                 "--port", port,
                 "--no-reload"],
                cwd=str(ecs_mcp_dir.absolute()),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        else:
            # 回退到 poetry run
            process = subprocess.Popen(
                ["poetry", "run", "serve"],
                cwd=str(ecs_mcp_dir.absolute()),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        
        manager.add_process(process, "ECS-MCP")
        
        # 等待端口就绪
        print(f"⏳ 等待 ECS MCP 服务器就绪 (端口 {ecs_port})...")
        if manager.wait_for_port("localhost", ecs_port, timeout=30):
            print(f"✅ ECS MCP 服务器已就绪 (端口 {ecs_port})")
            return True
        else:
            print(f"❌ ECS MCP 服务器启动超时 (端口 {ecs_port})")
            # 检查进程是否还在运行
            if process.poll() is not None:
                print(f"⚠️  ECS MCP 进程已退出，退出码: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ 启动 ECS MCP 服务器失败: {e}")
        return False


def start_k8s_mcp(manager: ProcessManager) -> bool:
    """启动 K8s MCP 服务器"""
    print("🚀 启动 K8s MCP 服务器...")
    
    k8s_mcp_dir = project_root / "k8s-mcp"
    if not k8s_mcp_dir.exists():
        print("⚠️  K8s MCP 目录不存在，跳过启动")
        return True  # 不是错误，只是跳过
    
    # 检查 poetry 环境
    try:
        result = subprocess.run(
            ["poetry", "env", "info", "--path"],
            cwd=k8s_mcp_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("⚠️  K8s MCP Poetry 环境未配置，尝试安装依赖...")
            subprocess.run(["poetry", "install"], cwd=k8s_mcp_dir, timeout=60)
    except Exception as e:
        print(f"⚠️  检查 K8s MCP 环境时出错: {e}")
        
    # 检查端口配置
    k8s_port = int(os.getenv("K8S_MCP_PORT", "8766"))
    
    # 启动 K8s MCP
    env = os.environ.copy()
    # 设置 PYTHONPATH，确保能找到 k8s_mcp 模块
    # poetry run 会自动设置环境，但我们还是显式设置 PYTHONPATH 以确保万无一失
    src_path = str(k8s_mcp_dir / "src")
    existing_pythonpath = env.get('PYTHONPATH', '')
    if existing_pythonpath:
        env['PYTHONPATH'] = f"{src_path}{os.pathsep}{existing_pythonpath}"
    else:
        env['PYTHONPATH'] = src_path
    # 不要清除 VIRTUAL_ENV，让 poetry 自己管理
    
    try:
        # 直接使用 poetry run serve，poetry 会自动处理环境
        # 确保在 k8s-mcp 目录下运行，poetry 会自动识别该目录的 pyproject.toml
        process = subprocess.Popen(
            ["poetry", "run", "serve"],
            cwd=str(k8s_mcp_dir.absolute()),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        manager.add_process(process, "K8s-MCP")
        
        # 等待端口就绪
        print(f"⏳ 等待 K8s MCP 服务器就绪 (端口 {k8s_port})...")
        if manager.wait_for_port("localhost", k8s_port, timeout=30):
            print(f"✅ K8s MCP 服务器已就绪 (端口 {k8s_port})")
            return True
        else:
            print(f"❌ K8s MCP 服务器启动超时 (端口 {k8s_port})")
            # 检查进程是否还在运行
            if process.poll() is not None:
                print(f"⚠️  K8s MCP 进程已退出，退出码: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ 启动 K8s MCP 服务器失败: {e}")
        return False


def start_backend(manager: ProcessManager):
    """启动后端服务器"""
    print("🚀 启动后端服务器...")
    
    backend_dir = project_root / "backend"
    if not backend_dir.exists():
        print("❌ 后端目录不存在")
        sys.exit(1)
        
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    env['ENV'] = os.getenv('ENV', 'production')
    
    # 启动后端
    cmd = [
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    print("=" * 60)
    print("🎉 所有服务已启动")
    print("📖 访问地址:")
    print("   主页: http://localhost:8000")
    print("   SPA应用: http://localhost:8000/spa/")
    print("   API文档: http://localhost:8000/docs")
    print("=" * 60)
    print("💡 按 Ctrl+C 停止所有服务")
    print()
    
    try:
        # 启动后端（主进程，会阻塞）
        process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            env=env
        )
        manager.add_process(process)
        process.wait()
    except KeyboardInterrupt:
        print("\n👋 收到停止信号")
    except Exception as e:
        print(f"❌ 后端服务器启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 启动钉钉运维机器人系统")
    print("=" * 60)
    print()
    
    manager = ProcessManager()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        # 1. 启动 ECS MCP 服务器
        if not start_ecs_mcp(manager):
            print("⚠️  ECS MCP 启动失败，继续启动其他服务...")
        
        # 2. 启动 K8s MCP 服务器
        if not start_k8s_mcp(manager):
            print("⚠️  K8s MCP 启动失败，继续启动其他服务...")
        
        # 3. 等待一下，确保 MCP 服务器完全就绪
        print("⏳ 等待 MCP 服务器完全就绪...")
        time.sleep(2)
        
        # 4. 启动后端服务器
        start_backend(manager)
        
    except KeyboardInterrupt:
        print("\n👋 收到停止信号")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
    finally:
        manager.stop_all()
        print("👋 所有服务已停止")


if __name__ == "__main__":
    main()


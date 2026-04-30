#!/usr/bin/env python3
"""
集成启动脚本
先启动 MCP 服务器，再启动后端服务器

MCP 子服务通过 MCP_SERVICE_SPECS 数据驱动，避免 ECS/K8s 两套重复逻辑。
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 项目根目录
project_root = Path(__file__).parent.parent


def log_output(process: subprocess.Popen, prefix: str):
    """在后台线程中输出进程日志"""

    def _log():
        try:
            for line in iter(process.stdout.readline, ""):
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
                if process.poll() is None:
                    print(f"正在停止进程 PID {process.pid}...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                print(f"停止进程时出错: {e}")


def _ensure_poetry_env(mcp_dir: Path) -> None:
    try:
        result = subprocess.run(
            ["poetry", "env", "info", "--path"],
            cwd=mcp_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            print("⚠️  Poetry 环境未配置，尝试安装依赖...")
            subprocess.run(["poetry", "install"], cwd=mcp_dir, timeout=120)
    except Exception as e:
        print(f"⚠️  检查 Poetry 环境时出错: {e}")


def _build_env_with_pythonpath(mcp_dir: Path) -> Dict[str, str]:
    env = os.environ.copy()
    src_path = str(mcp_dir / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing}" if existing else src_path
    return env


def _launch_uvicorn_from_venv(
    mcp_dir: Path,
    module: str,
    host: str,
    port: str,
    env: Dict[str, str],
) -> subprocess.Popen:
    result = subprocess.run(
        ["poetry", "env", "info", "-p"],
        cwd=str(mcp_dir.absolute()),
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        return subprocess.Popen(
            ["poetry", "run", "serve"],
            cwd=str(mcp_dir.absolute()),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    venv_path = Path(result.stdout.strip())
    uvicorn_exe = venv_path / "bin" / "uvicorn"
    if not uvicorn_exe.exists():
        uvicorn_exe = venv_path / "Scripts" / "uvicorn.exe"
    return subprocess.Popen(
        [
            str(uvicorn_exe),
            module,
            "--host",
            host,
            "--port",
            port,
            "--no-reload",
        ],
        cwd=str(mcp_dir.absolute()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


# K8s/ECS 已并入主应用进程（backend/src/k8s_mcp、backend/src/ecs_mcp），
# 此处不再拉起独立 MCP 子进程。历史独立工程见仓库 archived/ 目录。
MCP_SERVICE_SPECS: List[Dict[str, Any]] = []


def start_mcp_service(manager: ProcessManager, spec: Dict[str, Any]) -> bool:
    """按规范启动单个 MCP 子进程；目录不存在则跳过。"""
    title = spec["title"]
    subdir = spec["subdir"]
    mcp_dir = project_root / subdir

    print(f"🚀 启动 {title}...")
    if not mcp_dir.exists():
        print(f"⚠️  {subdir} 目录不存在，跳过启动")
        return True

    _ensure_poetry_env(mcp_dir)

    port = int(os.getenv(spec["port_env"], str(spec["default_port"])))
    he = spec.get("host_env")
    if he:
        host = os.getenv(he, spec.get("default_host") or "0.0.0.0")
    else:
        host = spec.get("default_host") or "0.0.0.0"
    env = _build_env_with_pythonpath(mcp_dir)
    for k, v in spec.get("env_extra", {}).items():
        env[k] = v

    try:
        launcher = spec["launcher"]
        if launcher == "uvicorn":
            process = _launch_uvicorn_from_venv(
                mcp_dir,
                spec["uvicorn_module"],
                host,
                str(port),
                env,
            )
        else:
            process = subprocess.Popen(
                ["poetry", "run", "serve"],
                cwd=str(mcp_dir.absolute()),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

        manager.add_process(process, spec["log_prefix"])
        print(f"⏳ 等待 {title} 就绪 (端口 {port})...")
        if manager.wait_for_port("localhost", port, timeout=30):
            print(f"✅ {title} 已就绪 (端口 {port})")
            return True
        print(f"❌ {title} 启动超时 (端口 {port})")
        if process.poll() is not None:
            print(f"⚠️  进程已退出，退出码: {process.returncode}")
        return False
    except Exception as e:
        print(f"❌ 启动 {title} 失败: {e}")
        return False


def start_backend(manager: ProcessManager):
    """启动后端服务器"""
    print("🚀 启动后端服务器...")

    backend_dir = project_root / "backend"
    if not backend_dir.exists():
        print("❌ 后端目录不存在")
        sys.exit(1)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    env["ENV"] = os.getenv("ENV", "production")

    cmd = [
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
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
        process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            env=env,
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

    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)

    try:
        for spec in MCP_SERVICE_SPECS:
            if not start_mcp_service(manager, spec):
                print(f"⚠️  {spec['title']} 启动失败，继续启动其他服务...")

        print("⏳ 等待 MCP 服务器完全就绪...")
        time.sleep(2)

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

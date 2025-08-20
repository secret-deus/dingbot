#!/usr/bin/env python3
"""
开发环境启动脚本
并行启动前端开发服务器和后端服务
"""

import subprocess
import sys
import time
import signal
from pathlib import Path
import threading

class DevServer:
    def __init__(self):
        self.processes = []
        self.project_root = Path(__file__).parent.parent
        
    def run_command(self, cmd, cwd=None, name=""):
        """在子进程中运行命令"""
        print(f"🚀 启动 {name}: {cmd}")
        try:
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(process)
            
            # 实时输出日志
            def log_output():
                for line in iter(process.stdout.readline, ''):
                    print(f"[{name}] {line.rstrip()}")
                    
            thread = threading.Thread(target=log_output)
            thread.daemon = True
            thread.start()
            
            return process
            
        except Exception as e:
            print(f"❌ 启动失败 {name}: {e}")
            return None
    
    def cleanup(self):
        """清理所有子进程"""
        print("\n🛑 正在停止服务...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ 所有服务已停止")
    
    def start(self):
        """启动开发服务器"""
        print("🚀 启动开发环境...")
        print("=" * 50)
        
        # 1. 启动后端服务
        backend_dir = self.project_root / "backend"
        backend_process = self.run_command(
            "python main.py",
            cwd=backend_dir,
            name="后端"
        )
        
        if not backend_process:
            print("❌ 后端启动失败")
            sys.exit(1)
        
        # 等待后端启动
        print("⏳ 等待后端启动...")
        time.sleep(3)
        
        # 2. 启动前端服务
        frontend_dir = self.project_root / "frontend"
        frontend_process = self.run_command(
            "npm run dev",
            cwd=frontend_dir,
            name="前端"
        )
        
        if not frontend_process:
            print("❌ 前端启动失败")
            self.cleanup()
            sys.exit(1)
        
        print("\n" + "=" * 50)
        print("🎉 开发环境启动成功！")
        print("📖 服务地址:")
        print("   前端开发服务: http://localhost:3000")
        print("   后端API服务: http://localhost:8000")
        print("   API文档: http://localhost:8000/docs")
        print("\n💡 提示:")
        print("   - 前端会自动代理API请求到后端")
        print("   - 前端支持热重载，修改即生效")
        print("   - 按 Ctrl+C 停止所有服务")
        print("=" * 50)
        
        try:
            # 等待用户中断
            while True:
                time.sleep(1)
                # 检查进程状态
                for process in self.processes:
                    if process.poll() is not None:
                        print(f"\n⚠️  有服务意外停止 (exit code: {process.returncode})")
                        self.cleanup()
                        sys.exit(1)
                        
        except KeyboardInterrupt:
            print("\n👋 收到停止信号...")
            self.cleanup()

def run_backend():
    """单独启动后端服务"""
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    
    print("🚀 启动后端开发服务...")
    try:
        subprocess.run(["python", "main.py"], cwd=backend_dir, check=True)
    except KeyboardInterrupt:
        print("\n👋 后端服务已停止")
    except Exception as e:
        print(f"❌ 后端启动失败: {e}")
        sys.exit(1)

def run_frontend():
    """单独启动前端服务"""
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    
    print("🚀 启动前端开发服务...")
    try:
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, check=True)
    except KeyboardInterrupt:
        print("\n👋 前端服务已停止")
    except Exception as e:
        print(f"❌ 前端启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    # 注册信号处理器
    server = DevServer()
    
    def signal_handler(signum, frame):
        server.cleanup()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server.start()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        server.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 
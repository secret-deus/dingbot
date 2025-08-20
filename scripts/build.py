#!/usr/bin/env python3
"""
项目构建脚本
编译前端并集成到后端static目录，准备生产部署
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil

def run_command(cmd, cwd=None):
    """运行命令并输出结果"""
    print(f"🔧 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ 命令失败: {cmd}")
        return False
    else:
        print(f"✅ 命令成功: {cmd}")
        return True

def build_frontend():
    """只构建前端项目"""
    print("🎨 构建前端项目...")
    
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    
    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        sys.exit(1)
    
    # 检查前端依赖
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 前端依赖未安装，正在安装...")
        if not run_command("npm install", cwd=frontend_dir):
            print("❌ 前端依赖安装失败")
            sys.exit(1)
    
    # 构建前端
    if not run_command("npm run build", cwd=frontend_dir):
        print("❌ 前端构建失败")
        sys.exit(1)
    
    print("✅ 前端构建完成！")

def clean():
    """清理构建文件"""
    print("🧹 清理构建文件...")
    
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    static_dir = backend_dir / "static"
    
    if static_dir.exists():
        shutil.rmtree(static_dir)
        print(f"✅ 删除静态文件: {static_dir}")
    
    # 清理前端构建产物
    frontend_dir = project_root / "frontend"
    dist_dir = frontend_dir / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"✅ 删除前端构建产物: {dist_dir}")
    
    print("✅ 清理完成！")

def main():
    """主函数"""
    print("🏗️  开始项目构建...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    backend_dir = project_root / "backend"
    static_dir = backend_dir / "static"
    
    print(f"📁 项目根目录: {project_root}")
    
    # 1. 检查前端目录
    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        sys.exit(1)
    
    # 2. 检查前端依赖
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 前端依赖未安装，正在安装...")
        if not run_command("npm install", cwd=frontend_dir):
            print("❌ 前端依赖安装失败")
            sys.exit(1)
    
    # 3. 清理旧的构建文件
    print("\n🧹 清理旧的构建文件...")
    if static_dir.exists():
        shutil.rmtree(static_dir)
        print(f"✅ 删除旧静态文件: {static_dir}")
    
    # 创建static目录
    static_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ 创建静态文件目录: {static_dir}")
    
    # 4. 构建前端
    print("\n🎨 构建前端项目...")
    if not run_command("npm run build", cwd=frontend_dir):
        print("❌ 前端构建失败")
        sys.exit(1)
    
    # 5. 检查构建结果
    spa_dir = static_dir / "spa"
    if not spa_dir.exists():
        print(f"❌ 前端构建输出不存在: {spa_dir}")
        sys.exit(1)
    
    # 6. 创建根目录index.html (重定向到SPA)
    print("\n📄 创建根目录index.html...")
    root_html = static_dir / "index.html"
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>钉钉K8s运维机器人</title>
    <script>
        // 自动重定向到SPA应用
        window.location.href = '/spa/';
    </script>
</head>
<body>
    <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
        <h2>🤖 钉钉K8s运维机器人</h2>
        <p>正在加载应用...</p>
        <p><a href="/spa/">点击这里手动进入</a></p>
    </div>
</body>
</html>'''
    
    with open(root_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ 创建重定向页面: {root_html}")
    
    # 7. 显示构建统计
    print("\n📊 构建统计:")
    
    # 统计文件数量和大小
    total_files = 0
    total_size = 0
    
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            file_path = Path(root) / file
            total_files += 1
            total_size += file_path.stat().st_size
    
    print(f"📁 静态文件总数: {total_files}")
    print(f"💾 静态文件总大小: {total_size / 1024 / 1024:.2f} MB")
    
    # 8. 验证关键文件
    key_files = [
        spa_dir / "index.html",
        static_dir / "index.html"
    ]
    
    print("\n🔍 验证关键文件:")
    for file_path in key_files:
        if file_path.exists():
            print(f"✅ {file_path.relative_to(project_root)}")
        else:
            print(f"❌ {file_path.relative_to(project_root)}")
    
    print("\n🎉 项目构建完成！")
    print("\n📖 下一步:")
    print("1. 启动服务: poetry run serve")
    print("2. 或直接运行: poetry run start")
    print(f"3. 访问: http://localhost:8000")

if __name__ == "__main__":
    main() 
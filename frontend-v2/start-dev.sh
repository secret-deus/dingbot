#!/bin/bash
# 钉钉K8s运维机器人 - 前端V2开发服务器启动脚本

echo "🚀 启动钉钉K8s运维机器人前端V2..."
echo ""

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 检测到依赖未安装，正在安装..."
    npm install
    echo ""
fi

echo "✨ 启动开发服务器..."
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo ""
echo "提示: 请确保后端服务已启动"
echo "后端启动命令: poetry run python backend/main.py"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

npm run dev

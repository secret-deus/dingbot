#!/usr/bin/env bash
# 首次安装依赖：加长 pip 超时 + 失败重试（缓解 files.pythonhosted.org Read timed out）
# 用法: ./scripts/poetry_install.sh
#       PIP_DEFAULT_TIMEOUT=600 ./scripts/poetry_install.sh --sync

set -euo pipefail

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info < (3, 14) else 1)' 2>/dev/null; then
  echo "[poetry_install.sh] 错误: 请勿使用 Python 3.14+（pydantic-core/PyO3 尚未支持）。请用 3.11–3.13，见 .python-version" >&2
  exit 2
fi

export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-300}"
export PIP_RETRIES="${PIP_RETRIES:-15}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

for attempt in 1 2 3; do
  echo "[poetry_install.sh] 第 ${attempt}/3 次: poetry install $*"
  if poetry install "$@"; then
    exit 0
  fi
  if [ "$attempt" -lt 3 ]; then
    wait=$((attempt * 8))
    echo "[poetry_install.sh] 失败，${wait}s 后重试…"
    sleep "$wait"
  fi
done

echo "[poetry_install.sh] 仍失败。可尝试："
echo "  1) 检查代理/VPN；2) 在 pyproject.toml 中启用国内 PyPI 镜像（已注释示例）；"
echo "  3) 增大超时: PIP_DEFAULT_TIMEOUT=600 ./scripts/poetry_install.sh"
exit 1

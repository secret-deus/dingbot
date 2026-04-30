"""
带重试与 pip 超时加长的 `poetry install` 包装。

首次安装请直接执行（勿用 poetry run，避免 entrypoint 未生成）:
  PIP_DEFAULT_TIMEOUT=300 python3 scripts/poetry_install.py
或:
  ./scripts/poetry_install.sh

参数与 ``poetry install`` 相同，例如 ``--sync``、``--no-root``。
"""

from __future__ import annotations

import os
import subprocess
import sys
import time


def main() -> int:
    if sys.version_info >= (3, 14):
        ver = ".".join(map(str, sys.version_info[:3]))
        print(
            f"错误：当前 Python {ver}。"
            "pydantic-core 在 3.14 上需源码编译，PyO3 目前仅支持到 3.13。"
            "请改用 3.11–3.13（见仓库 .python-version），例如: pyenv install 3.13 && pyenv local 3.13",
            file=sys.stderr,
        )
        return 2

    # pip 在 Poetry 安装子进程中会用到；默认 100s 在慢网下易超时
    os.environ.setdefault("PIP_DEFAULT_TIMEOUT", "300")
    os.environ.setdefault("PIP_RETRIES", "15")

    cmd = ["poetry", "install", *sys.argv[1:]]
    last_rc = 1
    for attempt in range(1, 4):
        print(f"[install-deps] 第 {attempt}/3 次: {' '.join(cmd)}", flush=True)
        last_rc = subprocess.call(cmd)
        if last_rc == 0:
            return 0
        if attempt < 3:
            wait = 8 * attempt
            print(f"[install-deps] 失败 (exit {last_rc})，{wait}s 后重试…", flush=True)
            time.sleep(wait)
    print("[install-deps] 仍失败：请检查网络/代理，或设置 PyPI 镜像后重试。", flush=True)
    return last_rc


if __name__ == "__main__":
    raise SystemExit(main())

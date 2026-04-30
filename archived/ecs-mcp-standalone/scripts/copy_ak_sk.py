#!/usr/bin/env python3
"""
复制阿里云 AK/SK 从 k8s-mcp/config.env 到 ecs-mcp/config.env

仅复制以下两个变量（若目标文件已存在相同键，不覆盖）：
- ALIBABA_CLOUD_ACCESS_KEY_ID
- ALIBABA_CLOUD_ACCESS_KEY_SECRET
"""

from pathlib import Path


SOURCE_FILE = Path(__file__).resolve().parents[2] / "k8s-mcp" / "config.env"
TARGET_FILE = Path(__file__).resolve().parents[1] / "config.env"
KEYS = [
    "ALIBABA_CLOUD_ACCESS_KEY_ID",
    "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
]


def parse_env(path: Path) -> dict:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def main():
    src = parse_env(SOURCE_FILE)
    dst = parse_env(TARGET_FILE)

    # 仅复制缺失的键
    changed = False
    lines = []
    if TARGET_FILE.exists():
        lines = TARGET_FILE.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    for key in KEYS:
        if key in dst:
            continue
        if key in src:
            lines.append(f"{key}={src[key]}")
            changed = True

    if changed:
        TARGET_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        print(f"✅ 已更新 {TARGET_FILE}")
    else:
        print("ℹ️ 无需更新：目标文件已包含所需键或源文件缺少对应键")


if __name__ == "__main__":
    main()






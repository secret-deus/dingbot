#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

run_in() {
  local dir="$1"
  shift
  echo
  echo "==> (${dir}) $*"
  (cd "${ROOT_DIR}/${dir}" && "$@")
}

run_root() {
  echo
  echo "==> $*"
  (cd "${ROOT_DIR}" && "$@")
}

run_in "backend-v2" poetry run pytest
run_in "frontend-v3" npm run build
run_in "mcp-servers/toolsearch" npm test
run_in "mcp-servers/toolsearch" npm audit --omit=dev

if command -v docker >/dev/null 2>&1; then
  run_root docker compose config
  if [[ "${VERIFY_DOCKER_BUILD:-0}" == "1" ]]; then
    run_root docker compose build
  else
    echo
    echo "==> docker compose build skipped; set VERIFY_DOCKER_BUILD=1 to run it."
  fi
else
  echo
  echo "==> docker not found; docker compose checks skipped."
fi

run_root git diff --check

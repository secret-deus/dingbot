#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

print_runtime_hint() {
  echo "==> Runtime hints"
  echo "python3: $(python3 --version 2>/dev/null || echo 'not found')"
  echo "node: $(node --version 2>/dev/null || echo 'not found')"
  if [[ -f "${ROOT_DIR}/.python-version" ]]; then
    echo "expected local Python: $(cat "${ROOT_DIR}/.python-version")"
  fi
  if [[ -f "${ROOT_DIR}/.nvmrc" ]]; then
    echo "expected local Node: $(cat "${ROOT_DIR}/.nvmrc")"
  fi
}

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

run_compose() {
  run_root docker compose --project-name ding-robot "$@"
}

print_runtime_hint
run_in "backend-v2" poetry run pytest
run_in "frontend-v3" npm run build
run_in "mcp-servers/toolsearch" npm test
if ! run_in "mcp-servers/toolsearch" npm audit --omit=dev; then
  echo
  echo "==> ToolSearch npm audit failed; retrying once after a short delay."
  sleep 2
  run_in "mcp-servers/toolsearch" npm audit --omit=dev
fi

if command -v docker >/dev/null 2>&1; then
  run_compose config
  if [[ "${VERIFY_DOCKER_BUILD:-0}" == "1" ]]; then
    run_compose build
  else
    echo
    echo "==> docker compose build skipped; set VERIFY_DOCKER_BUILD=1 to run it."
  fi
else
  echo
  echo "==> docker not found; docker compose checks skipped."
fi

run_root git diff --check

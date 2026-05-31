#!/usr/bin/env bash
set -euo pipefail

install_node() {
  local dir="$1"
  if [ -f "$dir/package.json" ]; then
    echo "==> node deps: $dir"
    if [ -f "$dir/pnpm-lock.yaml" ] && command -v pnpm >/dev/null; then
      (cd "$dir" && pnpm install --frozen-lockfile)
    elif [ -f "$dir/package-lock.json" ]; then
      (cd "$dir" && npm ci)
    else
      (cd "$dir" && npm install)
    fi
  fi
}

install_python() {
  local dir="$1"
  if [ -f "$dir/requirements.txt" ]; then
    echo "==> python deps: $dir"
    python3 -m pip install --upgrade pip
    python3 -m pip install -r "$dir/requirements.txt"
  elif [ -f "$dir/pyproject.toml" ]; then
    echo "==> python project: $dir"
    python3 -m pip install --upgrade pip
    (cd "$dir" && python3 -m pip install -e .)
  fi
}

for repo in /workspace/portfolio /workspace/dynamicsax /workspace/zerocode2md; do
  [ -d "$repo" ] || continue
  install_node "$repo"
  install_node "$repo/Frontend"
  install_python "$repo"
  install_python "$repo/Backend/api"
  install_python "$repo/Backend/bot"
done

echo "==> multi-repo install done"

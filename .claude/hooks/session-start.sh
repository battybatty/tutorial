#!/bin/bash
# SessionStart フック: Claude Code on the web のセッション開始時に依存パッケージを入れる。
# 依存マニフェストが存在するときだけ動く（現在のリポジトリには依存が無いので何もしない）。
set -euo pipefail

# Web（リモート）環境以外では何もしない
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Node.js
if [ -f package.json ]; then
  if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then
    pnpm install
  elif [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then
    yarn install
  else
    npm install
  fi
fi

# Python
if [ -f requirements.txt ]; then
  python3 -m pip install -r requirements.txt
elif [ -f pyproject.toml ]; then
  if command -v poetry >/dev/null 2>&1 && grep -q '^\[tool.poetry\]' pyproject.toml; then
    poetry install
  elif command -v uv >/dev/null 2>&1; then
    uv sync
  else
    python3 -m pip install -e .
  fi
fi

# Go
if [ -f go.mod ] && command -v go >/dev/null 2>&1; then
  go mod download
fi

# Rust
if [ -f Cargo.toml ] && command -v cargo >/dev/null 2>&1; then
  cargo fetch
fi

# Ruby
if [ -f Gemfile ] && command -v bundle >/dev/null 2>&1; then
  bundle install
fi

echo "session-start: 依存パッケージの確認が完了しました"

#!/usr/bin/env bash
# AgentWebSearchingTool 部署脚本
# 用法: ./scripts/deploy.sh [--skip-build]

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== AgentWebSearchingTool 部署 ==="

# ── 1. 环境检查 ──────────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || { echo "需要 Python 3.11+"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "需要 Node.js 20+"; exit 1; }

# ── 2. Build (可选跳过) ──────────────────────────────────────────────────
if [ "${1:-}" != "--skip-build" ]; then
  echo ">>> 构建 Engine..."
  cd engine
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e ".[dev]"
  cd ..

  echo ">>> 构建 mcp-server..."
  cd mcp-server && npm ci && npm run build && cd ..

  echo ">>> 构建 cli..."
  cd cli && npm ci && npm run build && cd ..
fi

# ── 3. 配置目录 ──────────────────────────────────────────────────────────
mkdir -p /opt/agent-web-search/{engine,mcp-server,cli,searxng-core}
mkdir -p /etc/agent-web-search

# ── 4. 复制文件 ──────────────────────────────────────────────────────────
cp -r engine/src engine/pyproject.toml engine/config.yaml /opt/agent-web-search/engine/
cp -r mcp-server/dist mcp-server/package.json /opt/agent-web-search/mcp-server/
cp -r cli/dist cli/package.json /opt/agent-web-search/cli/

# ── 5. 复制 systemd 服务 ────────────────────────────────────────────────
cp scripts/agent-web-search-engine.service /etc/systemd/system/
cp scripts/agent-web-search-mcp.service /etc/systemd/system/

echo ">>> 重新加载 systemd..."
systemctl daemon-reload

echo "=== 部署完成 ==="
echo "启动: systemctl start agent-web-search-engine"
echo "日志: journalctl -u agent-web-search-engine -f"

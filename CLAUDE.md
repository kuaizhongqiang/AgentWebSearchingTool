# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgentWebSearchingTool** — An AI Agent 网络搜索与智能筛选工具。提供 MCP Server 和 CLI 两种交付形态。

- **Repository**: <https://github.com/kuaizhongqiang/AgentWebSearchingTool>
- **SearXNG Fork**: <https://github.com/kuaizhongqiang/searxng>
- **License**: MIT (主体) / AGPL-3.0 (searxng-core/)
- **Milestones**: [GitHub Milestones](https://github.com/kuaizhongqiang/AgentWebSearchingTool/milestones)

### 当前状态 (M1 完成)

M1: SearXNG 清理 & 跑通 ✅ — 已完成。SearXNG Fork 精简完毕，JSON API 可正常返回搜索结果。

## 项目结构 (规划)

```
text
AgentWebSearchingTool/
├── searxng-core/          # SearXNG Fork (git submodule), AGPL-3.0
│                          #   → 打包进 engine/ wheel, 随 PyPI 发布
├── engine/                # Python 核心引擎, MIT
│   ├── scripts/           #   构建脚本 (prepare_build.py 打包 searxng-core)
│   ├── src/
│   │   ├── router.py      #   FastAPI 路由 + SearXNG 生命周期管理
│   │   ├── searxng_runner.py  # SearXNG 子进程管理器
│   │   └── ...
│   └── tests/             #   66 tests
├── mcp-server/            # MCP Server, MIT (TypeScript)
├── cli/                   # CLI 工具, MIT (TypeScript)
└── docs/                  # 设计文档
```

## Python Engine 开发

```bash
cd engine
python -m venv .venv
source .venv/Scripts/activate
pip install -e ".[dev]"

# 运行测试
pytest

# 启动开发服务
uvicorn src.router:app --reload --port 8000
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/search` | 执行搜索 |
| POST | `/fetch` | 抓取单页 |
| POST | `/scrape` | 批量抓取 |

### 配置

通过 `engine/config.yaml` 配置，支持环境变量覆盖: `SEARXNG_URL`, `ENGINE_PORT`。

## SearXNG-core 开发

### 环境

```bash
cd searxng-core
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

### 启动验证

```bash
cd searxng-core
source .venv/Scripts/activate
SEARXNG_SETTINGS_PATH=searx/settings.yml \
  SEARXNG_SECRET="your-secret" \
  python -m flask --app searx.webapp run --port 8888
```

### 搜索测试

```bash
# JSON API (未命中缓存时较慢，引擎 timeout 10s)
curl "http://127.0.0.1:8888/search?q=hello+world&format=json"

# 指定引擎可加快速度
curl "http://127.0.0.1:8888/search?q=hello&format=json&engines=wikipedia,brave"
```

### 代理配置

SearXNG 不读取系统 HTTP_PROXY 环境变量，需要在 `searxng-core/searx/settings.yml` 中配置：

```yaml
outgoing:
  proxies:
    all://:
      - socks5://127.0.0.1:10808
```

## Git 工作流

- `main` — 稳定分支，CI 自动打 tag
- `feat/*` — 功能分支
- `fix/*` — 修复分支
- 提交遵循 Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`

## MCP Memory Integration

`.mcp.json` 中配置了 `agent-memory` MCP 服务，使用 `tencent-agent-memory-mcp-bridge` 连接到 `https://memory.kuai-private.top/api/v1`。

工具: `store_memory`, `recall_memory`, `search_memories`, `end_session`。

调用约定：先 `mcp_get_tool_description` 获取参数 schema，再调用对应工具。

## 设计文档

- [docs/overview.md](docs/overview.md) — 项目定位与架构概览
- [docs/DESIGN.md](docs/DESIGN.md) — 模块详细设计
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — 开发指南
- [docs/PUBLISH.md](docs/PUBLISH.md) — 发布策略
- [docs/CI_CD.md](docs/CI_CD.md) — CI/CD 工作流

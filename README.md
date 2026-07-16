# AgentWebSearchingTool

面向 AI Agent 的网络搜索与智能筛选工具。提供 **MCP Server** 和 **CLI** 两种接入方式，核心基于 SearXNG 元搜索引擎。

## 项目结构

```
├── searxng-core/       # SearXNG Fork (git submodule), AGPL-3.0
│                       #   → 打包进 engine/ wheel, 随 PyPI 发布
├── engine/             # Python 核心引擎, MIT
│   ├── src/            #   FastAPI + 搜索/爬取/提取/检索 + SearXNG 进程管理
│   └── tests/          #   66 tests
├── mcp-server/         # MCP Server, MIT (TypeScript)
│   ├── src/            #   MCP 协议工具定义
│   └── tests/          #   24 tests
├── cli/                # CLI 工具, MIT (TypeScript)
│   ├── src/            #   awst 命令
│   └── tests/          #   13 tests
├── packages/types/     # 共享类型包
├── scripts/            # 部署脚本 + systemd 服务
└── docs/               # 设计文档
```

## 核心能力

| 能力 | 说明 | 技术 |
| --- | --- | --- |
| **多源搜索** | 聚合 100+ 搜索引擎，自托管无配额限制 | SearXNG Fork |
| **智能爬取** | HTTP 优先，JS 页面自动降级无头浏览器 | httpx + Playwright |
| **内容提取** | 自动提取正文、标题、作者、日期 | trafilatura |
| **向量检索** | Embedding 粗筛 + Cross-encoder 精排 | DashScope / LM Studio |
| **MCP Server** | AI Agent 通过 MCP 协议直接调用 | `@agent-web-search/types` |
| **CLI 工具** | 命令行搜索，支持管道和向量筛选 | awst |

## 快速开始

```bash
# 1. 启动 Engine (核心服务) — SearXNG 自动在后台启动
cd engine && pip install -e ".[dev,retrieval]"
uvicorn src.router:app --reload --port 8000                  # → localhost:8000

# 2. 启动 MCP Server (AI Agent 接入)
cd mcp-server && npm install && npm run build
ENGINE_URL=http://127.0.0.1:8000 node dist/index.js

# 3. 或用 CLI 直接使用
cd cli && npm install && npm run build && npm link
awst search "hello world"
```

## 安装

```bash
# Python 引擎
pip install agent-web-search-engine

# MCP Server
npx @kuaizhongqiang/mcp-server-agent-web-search

# CLI
npm install -g agent-web-search-cli
```

## 相关工作流

```bash
# 搜索 + 自动抓取 + 向量筛选
awst search "machine learning transformers" --fetch --filter -f json

# 管道模式: 搜索结果 → 筛选
awst search "AI" -f json | jq '.results[].content' | awst filter --query "deep learning"
```

## 开发

```bash
# Engine 测试
cd engine && pytest                    # 66 tests

# MCP Server 测试
cd mcp-server && npm test             # 24 tests

# CLI 测试
cd cli && npm test                    # 13 tests
```

## 许可证

- **engine / mcp-server / cli** — MIT
- **searxng-core/** — AGPL-3.0 (fork from [searxng/searxng](https://github.com/searxng/searxng))
  - 已打包在 `agent-web-search-engine` wheel 中，随 PyPI 发布

## 里程碑

| Milestone | 状态 | 内容 |
| --- | --- | --- |
| M1 | ✅ | SearXNG 清理 & 跑通 |
| M2 | ✅ | Python Engine 核心 |
| M3 | ✅ | 向量检索 |
| M4 | ✅ | MCP Server + CLI |
| M5 | ✅ | CI/CD + 部署 |
| M6 | 🏗 | 文档完善 |


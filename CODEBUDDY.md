# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## Project Overview

AgentWebSearchingTool — AI Agent 专用的网络搜索与智能筛选工具。双入口交付：MCP Server（Agent 调用）+ CLI（人/脚本使用）。核心引擎 Python，MCP/CLI 层 TypeScript。

## Commands

No build/lint/test toolchain configured yet. Add commands here as they are established.

## Architecture

```
Agent (MCP Client) / User (CLI)
        │
        ▼
┌──────────────────────────┐
│  MCP Server (TypeScript) │  ← MCP 协议工具定义、会话管理、结果缓存
│  CLI        (TypeScript) │  ← 命令行入口，支持管道模式
└──────────┬───────────────┘
           │ HTTP / subprocess
           ▼
┌──────────────────────────┐
│  Python Engine            │  你的家用服务器 (i5-12th/16G/1T)
│  ├─ 路由 & 编排           │
│  ├─ 搜索源: SearXNG Fork  │  ← searxng-core/ (AGPL-3.0, 独立进程)
│  ├─ 爬取: 混合策略        │  HTTP → Playwright 降级
│  ├─ 提取: trafilatura     │
│  └─ 检索: 两阶段向量检索  │  Embedding API → Cross-encoder 精排
└──────────────────────────┘
```

### 关键设计决策

- **搜索源**：Fork SearXNG 并精简（去 Docker/UI），作为独立进程通过 HTTP API 调用。保持 AGPL-3.0，与 MIT 主项目进程隔离。
- **Embedding**：Provider 抽象层。默认阿里云 DashScope API，可切换 Tailscale + LM Studio 本地模式。
- **爬取策略**：先轻量 HTTP 请求，JS 渲染页面降级到 Playwright。
- **许可证**：主体 MIT。searxng-core/ 保持 AGPL-3.0。Apache 2.0 依赖需加署名声明。

### Repository Layout (Planned)

```
AgentWebSearchingTool/
├── searxng-core/      # SearXNG Fork, AGPL-3.0, 独立子目录
├── engine/            # Python Engine, MIT — 搜索编排、爬虫、提取、检索
├── mcp-server/        # MCP Server, MIT — TypeScript
├── cli/               # CLI, MIT — TypeScript
└── docs/              # 设计文档
```

### License Compliance

- `searxng-core/` — AGPL-3.0, fork from searxng/searxng, process-isolated
- All other directories — MIT
- Apache 2.0 dependencies (e.g., crawl4ai patterns) require attribution in NOTICE
- AGPL components run as separate processes, accessed via HTTP API only

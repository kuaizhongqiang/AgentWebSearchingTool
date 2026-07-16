# AgentWebSearchingTool

面向 AI Agent 的网络搜索与智能筛选工具。

## 定位

不是给人用的搜索界面，是给 AI Agent 调用的工具。提供 MCP Server 和 CLI 两种接入方式。

## 核心能力

- **多源搜索** — 基于 SearXNG 引擎聚合，100+ 搜索引擎，自托管无配额限制
- **智能爬取** — 混合策略（HTTP 优先，无头浏览器降级），兼顾效率与覆盖率
- **向量检索筛选** — Embedding 粗筛 + Cross-encoder 精排，从搜索结果中精准定位相关内容
- **MCP Server** — 标准 MCP 协议，Agent 直接调用 `web_search`、`web_fetch` 等工具
- **CLI 工具** — 命令行直接使用，支持管道模式，方便脚本集成

## 技术栈

- **Python** — 搜索引擎核心 + 爬虫 + 内容提取 + 向量检索
- **TypeScript** — MCP Server + CLI
- **SearXNG** (Fork) — 元搜索引擎，AGPL-3.0，独立进程隔离

## 许可证

本项目主体使用 MIT 许可证。`searxng-core/` 目录 fork 自 [searxng/searxng](https://github.com/searxng/searxng)，保持 AGPL-3.0。

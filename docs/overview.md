# AgentWebSearchingTool 项目概述

## 一、项目定位

AgentWebSearchingTool 是一个面向 AI Agent 的网络搜索与智能筛选工具。与传统的面向人类的搜索引擎不同，它的目标用户是 AI Agent——Agent 通过 MCP 协议直接调用搜索、爬取、筛选能力，获取结构化、去噪后的网页信息。

项目提供两种交付形态：**MCP Server**（供 Agent 集成调用）和 **CLI 工具**（供开发者/脚本直接使用），两者共享同一套 Python 核心引擎。

## 二、核心能力分层

**搜索源层** — Fork SearXNG 并精简（移除 Docker 依赖和 Web UI），作为元搜索引擎聚合 Google、Bing、DuckDuckGo 等 100+ 搜索引擎的结果。以独立进程运行，通过 HTTP API 供上层调用。保持原项目 AGPL-3.0 许可证，进程隔离确保不传染主项目。

**爬取层** — 采用混合策略：优先使用轻量 HTTP 请求获取页面内容，遇到 JavaScript 渲染页面时降级到 Playwright 无头浏览器。在效率与覆盖率之间取得平衡，同时通过合理的请求频率控制遵守 robots.txt 规范。

**内容提取层** — 使用 trafilatura 进行自动正文提取，将 HTML 页面转化为结构化纯文本，为后续检索筛选做准备。

**检索筛选层** — 两阶段向量检索。第一阶段用 Embedding 模型对所有搜索结果做语义粗筛，第二阶段用 Cross-encoder 模型对候选集做精细排序。Embedding 通过 Provider 抽象层接入，默认使用阿里云 DashScope API，支持通过 Tailscale 组网降级到本地 LM Studio，兼顾成本与灵活性。

**接入层** — TypeScript 实现的 MCP Server 和 CLI。MCP Server 暴露 `web_search`、`web_fetch` 等标准工具供 Agent 调用；CLI 支持单次搜索和管道模式，方便脚本集成。

## 三、技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| 搜索引擎核心 | Python | 路由编排、爬虫、提取、检索 |
| 接入层 | TypeScript | MCP Server + CLI |
| 搜索源 | SearXNG (Fork) | 去容器化精简版，AGPL-3.0 |
| 内容提取 | trafilatura | 自动正文提取 |
| 爬虫 | requests + Playwright | 混合策略，HTTP 优先 |
| Embedding | DashScope API / LM Studio | Provider 抽象，双模式可切换 |
| 向量检索 | 两阶段（粗筛+精排） | Embedding + Cross-encoder |
| 部署 | 家用服务器 + Cloudflare | i5-12代 / 16GB / 1TB SSD |

## 四、部署架构

核心引擎部署在一台家用服务器（i5-12代 / 16GB 内存 / 1TB SSD）上，通过 Cloudflare 代理的公网域名对外暴露 MCP Server。SearXNG-core 仅开内网端口。向量模型的本地降级方案通过 Tailscale 组网连接到另一台 GPU 机器上的 LM Studio。

## 五、仓库结构（规划）

```
AgentWebSearchingTool/
├── searxng-core/      # SearXNG Fork, AGPL-3.0, 独立进程
├── engine/            # Python 核心引擎, MIT
├── mcp-server/        # MCP Server, MIT (TypeScript)
├── cli/               # CLI 工具, MIT (TypeScript)
└── docs/              # 设计文档
```

## 六、许可证策略

| 组件 | 许可证 | 备注 |
|------|--------|------|
| engine / mcp-server / cli | MIT | 项目主体 |
| searxng-core/ | AGPL-3.0 | Fork 自 searxng/searxng，进程隔离 |
| 外部依赖 (Apache 2.0) | — | 在 NOTICE 文件中署名声明 |

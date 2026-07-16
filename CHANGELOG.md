# Changelog

## [0.0.0] - 2026-07-16

### M1: SearXNG 清理 & 跑通
- Fork SearXNG, 移除 Docker/Web UI/文档/测试等冗余文件
- 精简 settings.yml (88KB→240行), 保留 23 个常用引擎
- Windows 兼容性修复 (pwd, valkeydb)
- 轻量 babel 替代层恢复 Google/Wikipedia 等 18 个引擎

### M2: Python Engine 核心
- SearchProvider 接口 + SearXNG HTTP 适配器
- FetchEngine HTTP+Playwright 混合爬取
- ExtractEngine trafilatura 内容提取
- FastAPI Router (/health, /search, /fetch, /scrape)

### M3: 向量检索
- EmbeddingProvider 抽象层 (DashScope + LM Studio)
- 两阶段检索管道 (Embedding 粗筛 + Cross-encoder 精排)
- /filter 端点集成

### M4: MCP Server + CLI
- MCP Server: web_search/web_fetch/web_scrape/search_filter 工具
- CLI: awst search/fetch/scrape/filter/config/serve 命令
- 会话管理 + 管道模式
- 共享类型包 packages/types

### M5: CI/CD + 部署
- GitHub Actions CI (commitlint + test + typecheck)
- semantic-release 自动版本管理
- PyPI + npm 自动发布
- systemd 部署服务

# MCP Server — Agent Web Search

为 AI Agent 提供网络搜索能力的 MCP Server。通过标准 MCP 协议暴露 `web_search`、`web_fetch`、`web_scrape`、`search_filter` 工具。

## 快速开始

```bash
cd mcp-server
npm install
npm run build

# 确保 Python Engine 运行在 8000 端口
ENGINE_URL=http://127.0.0.1:8000 node dist/index.js
```

## MCP 客户端配置

在 Claude Desktop 或任何 MCP 客户端中添加:

```json
{
  "mcpServers": {
    "web-search": {
      "command": "node",
      "args": ["path/to/mcp-server/dist/index.js"],
      "env": { "ENGINE_URL": "http://127.0.0.1:8000" }
    }
  }
}
```

## 工具列表

| 工具 | 参数 | 说明 |
|------|------|------|
| `web_search` | query, num_results?, engine? | 搜索网页，返回 `session_id` |
| `web_search_page` | session_id, page, page_size? | 分页获取已缓存的搜索结果 |
| `web_fetch` | url, extract_mode? | 抓取单页并提取正文 |
| `web_scrape` | urls[], extract_mode? | 批量抓取多页 (≤20) |
| `search_filter` | query, results[], top_k? | 向量相似度筛选文档 |

## 会话管理

`web_search` 返回 `session_id`，结果在服务端缓存 5 分钟。
使用 `web_search_page` 可分页遍历结果，避免重复请求 Engine。

## 测试

```bash
npm test          # 24 tests (unit + integration)
npm run typecheck # TypeScript 类型检查
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENGINE_URL` | `http://127.0.0.1:8000` | Python Engine 地址 |

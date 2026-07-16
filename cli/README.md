# CLI — Agent Web Search (`awst`)

命令行网络搜索工具，支持管道模式和向量筛选。

## 安装

```bash
# 全局安装
npm install -g agent-web-search-cli

# 或本地开发
cd cli && npm install && npm run build && npm link
```

## 命令

### search — 搜索

```bash
awst search "query"                       # 默认 text 格式
awst search "query" -n 5 -e google        # 5 条结果，Google 引擎
awst search "query" --fetch               # 自动抓取页面内容
awst search "query" --filter              # 向量筛选结果
awst search "query" -f json               # JSON 输出
```

### fetch — 抓取单页

```bash
awst fetch https://example.com            # 抓取 + 提取正文
awst fetch https://example.com -f json    # JSON 输出
```

### scrape — 批量抓取

```bash
awst scrape https://a.com https://b.com   # 抓取多页
```

### filter — 向量筛选

```bash
awst filter --query "python" "doc1 text" "doc2 text"
```

### 管道模式

```bash
awst search "machine learning" -f json | jq '.results[].content' | awst filter --query "deep learning"
echo -e "doc1\ndoc2\ndoc3" | awst filter --query "relevant topic"
```

### config — 配置

```bash
awst config          # 显示当前配置
```

### serve — MCP Server 模式

```bash
awst serve           # 启动 MCP Server (stdio)
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENGINE_URL` | `http://127.0.0.1:8000` | Python Engine 地址 |
| `MCP_SERVER_PATH` | `../mcp-server/dist/index.js` | MCP Server 路径 |

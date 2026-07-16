# 架构设计文档

## 1. 总体架构

```
                         ┌─────────────────────────┐
  Agent (MCP Client) ──→ │  MCP Server (TS)        │
                         │  - web_search            │
                         │  - web_fetch             │
  User / Script ───────→ │  - web_scrape            │
                         │  - search_filter         │
                         └───────────┬─────────────┘
                                     │ HTTP REST
                         ┌───────────▼─────────────┐
                         │  Python Engine           │
                         │  ┌─────────────────────┐ │
                         │  │ Router / Orchestrator│ │
                         │  └─────────┬───────────┘ │
                         │            │             │
                         │  ┌─────────▼───────────┐ │
                         │  │ Search Provider     │ │  ← Provider 接口
                         │  │  └─ SearXNG Adapter │ │
                         │  │  └─ (Future: Custom)│ │
                         │  └─────────┬───────────┘ │
                         │            │             │
                         │  ┌─────────▼───────────┐ │
                         │  │ Fetch Engine        │ │
                         │  │  ├─ HTTP Fetcher    │ │
                         │  │  └─ Playwright      │ │
                         │  └─────────┬───────────┘ │
                         │            │             │
                         │  ┌─────────▼───────────┐ │
                         │  │ Extract Engine      │ │
                         │  │  └─ trafilatura     │ │
                         │  └─────────┬───────────┘ │
                         │            │             │
                         │  ┌─────────▼───────────┐ │
                         │  │ Retrieval Pipeline  │ │
                         │  │  ├─ EmbeddingProvider│ │  ← Provider 抽象
                         │  │  ├─ VectorStore      │ │
                         │  │  └─ CrossEncoder    │ │
                         │  └─────────────────────┘ │
                         └───────────────────────────┘
                                     │ HTTP REST
                         ┌───────────▼─────────────┐
                         │  SearXNG-core (AGPL-3.0)│
                         │  独立进程, localhost:8888 │
                         └───────────────────────────┘
```

## 2. 模块详细设计

### 2.1 MCP Server (TypeScript)

**工具定义：**

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `web_search` | query, num_results?, engine? | SearchResult[] | 执行搜索，返回结果列表 |
| `web_fetch` | url, extract_mode? | PageContent | 获取单个页面内容 |
| `web_scrape` | urls[], extract_mode? | PageContent[] | 批量抓取多个页面 |
| `search_filter` | query, results[] | FilteredResult[] | 对已有结果做向量筛选 |

**会话管理：**
- 每次搜索会话生成 session_id
- 搜索结果缓存在 Engine 侧，避免重复请求
- 支持分页获取（对大量结果）

**与 Engine 通信：**
- 通过 HTTP REST 调用 Engine API
- 或 subprocess spawn Python Engine 进程
- 支持流式返回大内容

### 2.2 CLI (TypeScript)

**命令设计：**

```
awst search "query"                    # 搜索
  --num 10                             # 返回数量
  --engine google                      # 指定搜索引擎
  --filter                             # 启用向量筛选
  --fetch                              # 自动抓取页面内容

awst fetch <url>                       # 抓取单页
awst scrape <url1> <url2> ...          # 批量抓取
awst config                            # 查看/修改配置
awst serve                             # 启动 MCP Server 模式
```

**管道模式：**
```
echo "search results json" | awst filter --query "相关的内容"
```

### 2.3 Python Engine

#### 2.3.1 Router / Orchestrator

入口模块，接收请求后编排各层调用：

```
search(query) → SearchProvider.search()
              → [for each result] FetchEngine.fetch()
              → ExtractEngine.extract()
              → [if filter enabled] RetrievalPipeline.run()
              → 返回结构化结果
```

#### 2.3.2 Search Provider

```
class SearchProvider(ABC):
    @abstractmethod
    def search(query: str, num: int, engine: str) -> list[SearchResult]

class SearXNGProvider(SearchProvider):
    # 通过 HTTP 调 searxng-core API

class CustomProvider(SearchProvider):
    # 未来扩展：自建搜索引擎聚合
```

#### 2.3.3 Fetch Engine

混合策略实现：

```
async def fetch(url: str) -> PageContent:
    result = await http_fetch(url)       # 先用 requests/httpx
    if result.needs_js():
        result = await browser_fetch(url) # 降级到 Playwright
    return result
```

配置项：
- 全局请求间隔（默认 1s）
- 单域名并发数（默认 2）
- robots.txt 检查开关
- User-Agent 轮换策略

#### 2.3.4 Extract Engine

```
class ExtractEngine:
    def extract(html: str, url: str) -> ExtractedContent:
        doc = trafilatura.extract(html, include_comments=False)
        return ExtractedContent(
            title=doc.title,
            text=doc.text,
            metadata={...}
        )
```

#### 2.3.5 Retrieval Pipeline

```
class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(texts: list[str]) -> list[list[float]]:
        """返回向量列表"""

class DashScopeProvider(EmbeddingProvider):
    # 阿里云 text-embedding-v4

class LMStudioProvider(EmbeddingProvider):
    # LM Studio OpenAI-compatible API
    # 通过 Tailscale 内网 IP 连接

class RetrievalPipeline:
    def run(query: str, documents: list[Document]) -> list[ScoredDoc]:
        # Stage 1: Embedding 粗筛
        query_vec = embedder.embed([query])[0]
        doc_vecs = embedder.embed([d.text for d in documents])
        candidates = top_k_cosine(query_vec, doc_vecs, k=20)

        # Stage 2: Cross-encoder 精排
        scores = cross_encoder.score(query, [c.text for c in candidates])
        return sorted(zip(candidates, scores), reverse=True)[:5]
```

### 2.4 SearXNG-core

- Fork 自 searxng/searxng，去除：Docker 相关文件、Web UI、多语言界面、用户认证
- 保留：搜索引擎适配器、结果聚合去重、JSON API (`/search?format=json`)
- 作为独立 Python 进程运行，监听 `127.0.0.1:8888`
- 通过 `git subtree` 跟踪上游，定期 merge 更新适配器

## 3. 配置管理

单一配置文件 `config.yaml`（或 `.env`）：

```yaml
# 搜索配置
search:
  provider: searxng              # searxng | custom
  searxng_url: http://127.0.0.1:8888
  default_engine: google
  max_results: 20

# 爬取配置
fetch:
  strategy: hybrid               # http | browser | hybrid
  request_interval: 1.0          # 秒
  max_concurrent: 5
  respect_robots_txt: true
  user_agent_rotation: true

# 提取配置
extract:
  engine: trafilatura
  max_content_length: 10000

# 检索配置
retrieval:
  embedding:
    provider: dashscope          # dashscope | lmstudio
    dashscope:
      api_key: ${DASHSCOPE_API_KEY}
      model: text-embedding-v4
    lmstudio:
      base_url: http://100.x.x.x:1234/v1  # Tailscale IP
      model: qwen-embedding
  cross_encoder:
    model: BAAI/bge-reranker-base
  top_k: 5

# 服务配置
server:
  host: 0.0.0.0
  port: 8000
```

## 4. 数据流

```
用户/Agent 请求
  │
  ▼
[CLI / MCP Server]
  │ 构造请求参数
  ▼
[Python Engine Router]
  │
  ├─→ [SearchProvider] ──→ SearXNG API ──→ 搜索结果列表
  │
  ├─→ [FetchEngine] ──→ 并发抓取各结果URL
  │       │
  │       ├─ HTTP (成功) → 返回HTML
  │       └─ HTTP (失败/JS页面) → Playwright → 返回HTML
  │
  ├─→ [ExtractEngine] ──→ trafilatura 提取正文
  │
  ├─→ [RetrievalPipeline] (可选，filter模式)
  │       │
  │       ├─ EmbeddingProvider.embed() → 向量
  │       ├─ cosine_similarity → top-20 候选
  │       └─ CrossEncoder.score() → top-5 结果
  │
  ▼
结构化 JSON 响应
  │
  ▼
[CLI 输出 / MCP 返回给 Agent]
```

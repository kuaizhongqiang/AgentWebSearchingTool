# 开发文档

## 1. 环境准备

### 前置依赖

- Python 3.11+
- Node.js 20+
- Playwright（用于浏览器降级爬取）
- Git

### 初始化

```bash
# 克隆仓库（含 searxng-core submodule）
git clone --recurse-submodules <repo-url>
cd AgentWebSearchingTool

# Python Engine
cd engine
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# MCP Server + CLI
cd ../mcp-server
npm install

cd ../cli
npm install
```

### SearXNG-core 部署

```bash
cd searxng-core
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 配置 settings.yml（仅保留必要项）
python searx/webapp.py  # 监听 127.0.0.1:8888
```

## 2. 开发工作流

### 项目结构

```
AgentWebSearchingTool/
├── searxng-core/          # SearXNG Fork (git submodule), AGPL-3.0
├── engine/                # Python 核心引擎, MIT
│   ├── src/
│   │   ├── router.py      # 路由编排
│   │   ├── search/        # SearchProvider 接口 + 实现
│   │   ├── fetch/         # FetchEngine (HTTP + Playwright)
│   │   ├── extract/       # ExtractEngine (trafilatura)
│   │   ├── retrieval/     # RetrievalPipeline (Embedding + Rerank)
│   │   └── config.py      # 配置加载
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
├── mcp-server/            # MCP Server, MIT (TypeScript)
│   ├── src/
│   │   ├── index.ts       # MCP Server 入口
│   │   ├── tools/         # 工具定义 (web_search, web_fetch, ...)
│   │   └── client.ts      # Engine HTTP 客户端
│   ├── package.json
│   └── tsconfig.json
├── cli/                   # CLI 工具, MIT (TypeScript)
│   ├── src/
│   │   └── index.ts       # CLI 入口 (commander)
│   ├── package.json
│   └── tsconfig.json
└── docs/                  # 设计 & 开发文档
```

### 开发流程

1. **创建 Feature Branch**：`git checkout -b feat/xxx`
2. **编码**：修改对应模块
3. **本地测试**：
   ```bash
   # Python 测试
   cd engine && pytest

   # TypeScript 类型检查
   cd mcp-server && npx tsc --noEmit
   cd cli && npx tsc --noEmit
   ```
4. **提交**：遵循 Conventional Commits（`feat:`, `fix:`, `docs:`, `refactor:`）
5. **提 PR** → CI 自动运行 lint + test + typecheck → 合并

### 分支策略

- `main` — 稳定分支，CI 自动打 tag
- `feat/*` — 功能分支
- `fix/*` — 修复分支
- `docs/*` — 文档分支

## 3. Python Engine 开发

### 启动开发服务

```bash
cd engine
uvicorn src.router:app --reload --port 8000
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/search` | 执行搜索 |
| POST | `/fetch` | 抓取单页 |
| POST | `/scrape` | 批量抓取 |
| POST | `/filter` | 向量筛选已有结果 |
| GET | `/health` | 健康检查 |

### 添加新的 SearchProvider

```python
# engine/src/search/custom_provider.py
from engine.src.search.base import SearchProvider, SearchResult

class CustomProvider(SearchProvider):
    async def search(self, query: str, num: int = 10) -> list[SearchResult]:
        # 实现你的搜索逻辑
        pass
```

### 添加新的 EmbeddingProvider

```python
# engine/src/retrieval/embedding_provider.py
from engine.src.retrieval.base import EmbeddingProvider

class NewProvider(EmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]:
        # 实现你的 Embedding 逻辑
        pass
```

## 4. TypeScript 开发

### MCP Server

```bash
cd mcp-server
npm run dev          # 开发模式
npm run build        # 构建
```

**添加新工具：**

```typescript
// mcp-server/src/tools/my_tool.ts
import { z } from "zod";

export const myToolSchema = z.object({
  param: z.string().describe("参数说明"),
});

export async function myToolHandler(args: z.infer<typeof myToolSchema>) {
  // 调 Engine API
  const result = await engineClient.post("/my-endpoint", args);
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
}
```

### CLI

```bash
cd cli
npm run dev          # 开发模式
npm run build        # 构建
npm link             # 全局安装 awst 命令（本地开发用）
```

## 5. 测试

### Python

```bash
cd engine
pytest                          # 全部测试
pytest tests/test_search.py     # 单个文件
pytest -v -k "test_fetch"       # 按名称筛选
```

### TypeScript

```bash
cd mcp-server && npm test
cd cli && npm test
```

## 6. 上游 SearXNG 同步

```bash
cd searxng-core
git remote add upstream https://github.com/searxng/searxng.git
git fetch upstream
git merge upstream/master       # 定期同步上游更新
# 解决冲突，优先保留我们的精简改动
```

## 7. 依赖管理

### Python 核心依赖

```
fastapi, uvicorn          # Web 框架
httpx                     # 异步 HTTP 客户端
trafilatura               # 内容提取
playwright                # 浏览器自动化
sentence-transformers     # Cross-encoder
dashscope                 # 阿里云 Embedding API
openai                    # LM Studio OpenAI-compatible API
numpy, scipy              # 向量计算
pyyaml                    # 配置解析
```

### TypeScript 核心依赖

```
@modelcontextprotocol/sdk  # MCP SDK
commander                   # CLI 框架
zod                         # 参数校验
```

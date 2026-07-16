# Agent Web Search Engine

Python 核心引擎，提供搜索编排、网页爬取、内容提取和向量检索能力。

**SearXNG-core** 已打包在 wheel 中，安装后引擎自动管理 SearXNG 子进程，无需额外部署。

## 快速开始

```bash
# 克隆仓库（含 searxng-core submodule）
git clone --recurse-submodules <repo-url>
cd AgentWebSearchingTool/engine

# 打包 searxng-core 到包中（仅开发模式需要）
python scripts/prepare_build.py

# 创建虚拟环境并安装
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev,retrieval]"

# 运行测试
pytest

# 启动服务（SearXNG 会自动在后台启动）
uvicorn src.router:app --reload --port 8000
```

> **pip 安装用户**: `pip install agent-web-search-engine` 后，SearXNG 已内置在包中，引擎会自动启动它。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（含 SearXNG 状态） |
| POST | `/search` | 执行搜索（自动使用内置 SearXNG） |
| POST | `/fetch` | 抓取单页 + 内容提取 |
| POST | `/scrape` | 批量抓取多页 |
| POST | `/filter` | 向量检索筛选 |

## 模块架构

```
src/
├── router.py            # FastAPI 路由编排（含 SearXNG 生命周期管理）
├── searxng_runner.py    # SearXNG 子进程管理器（启动/停止/健康检查）
├── config.py            # YAML 配置加载
├── search/              # SearchProvider 接口 + SearXNG 适配器
├── fetch/               # HTTP + Playwright 混合爬取
├── extract/             # trafilatura 内容提取
└── retrieval/           # Embedding + Cross-encoder 两阶段检索
```

## 配置

编辑 `config.yaml` 或通过环境变量覆盖:

```bash
# SearXNG 配置（内置，通常无需修改）
SEARXNG_PORT=8888
SEARXNG_BIND_ADDRESS=127.0.0.1
SEARXNG_SECRET=my-secret-key      # 建议设置

# Engine 配置
SEARXNG_URL=http://127.0.0.1:8888
ENGINE_PORT=8000
DASHSCOPE_API_KEY=sk-xxx          # DashScope Embedding
```

## 依赖

| 用途 | 安装方式 |
|------|----------|
| 核心（含 SearXNG-core） | `pip install agent-web-search-engine` |
| 开发 + 测试 | `pip install -e ".[dev]"` |
| 检索 | `pip install -e ".[retrieval]"` (dashscope, openai, torch, transformers) |
| 浏览器爬取 | `pip install -e ".[playwright]"` + `playwright install chromium` |

## License

- Engine 代码: MIT
- Bundled SearXNG-core: AGPL-3.0-or-later

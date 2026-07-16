# Agent Web Search Engine

Python 核心引擎，提供搜索编排、网页爬取、内容提取和向量检索能力。

## 快速开始

```bash
cd engine
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev,retrieval]"
pytest                        # 66 tests

# 启动服务
uvicorn src.router:app --reload --port 8000
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/search` | 执行搜索（需 SearXNG 运行在 8888 端口） |
| POST | `/fetch` | 抓取单页 + 内容提取 |
| POST | `/scrape` | 批量抓取多页 |
| POST | `/filter` | 向量检索筛选 |

## 模块架构

```
src/
├── router.py         # FastAPI 路由编排
├── config.py         # YAML 配置加载
├── search/           # SearchProvider 接口 + SearXNG 适配器
├── fetch/            # HTTP + Playwright 混合爬取
├── extract/          # trafilatura 内容提取
└── retrieval/        # Embedding + Cross-encoder 两阶段检索
```

## 配置

编辑 `config.yaml` 或通过环境变量覆盖:

```bash
SEARXNG_URL=http://127.0.0.1:8888
ENGINE_PORT=8000
DASHSCOPE_API_KEY=sk-xxx    # DashScope Embedding
```

## 依赖

| 用途 | 安装方式 |
|------|----------|
| 核心 | `pip install -e .` |
| 开发 + 测试 | `pip install -e ".[dev]"` |
| 检索 | `pip install -e ".[retrieval]"` (dashscope, openai, torch, transformers) |
| 浏览器爬取 | `pip install -e ".[playwright]"` + `playwright install chromium` |

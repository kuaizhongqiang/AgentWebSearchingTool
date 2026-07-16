# Agent Web Search Engine

Python 核心引擎，提供搜索编排、网页爬取和内容提取能力。

## 快速开始

```bash
pip install -e ".[dev]"

# 启动服务
uvicorn src.router:app --reload --port 8000

# 运行测试
pytest
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/search` | 执行搜索 |
| POST | `/fetch` | 抓取单页 |
| POST | `/scrape` | 批量抓取 |

## 配置

编辑 `config.yaml` 或设置环境变量 `SEARXNG_URL`, `ENGINE_PORT`。

# SearXNG-core 接口文档

## 概述

SearXNG-core 是精简后的 SearXNG，仅保留 JSON API 能力。服务监听 `127.0.0.1:8888`，对外提供搜索相关的 HTTP 接口。

## 输出格式

默认仅支持 `json` 格式（精简后移除 `html`/`csv`/`rss`）。

---

## API 端点

### 1. GET /healthz — 健康检查

检测服务是否正常运行。

**请求：**
```
GET /healthz
```-

**响应：**
```
HTTP 200
Content-Type: text/plain

OK
```

---

### 2. GET /search — 搜索 ⭐

核心搜索接口。所有搜索请求通过此端点完成。

**请求：**
```
GET /search?q={query}&format=json&pageno={page}&language={lang}&time_range={range}&categories={cats}&engines={engines}
```

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | **是** | — | 搜索关键词 |
| `format` | string | 否 | `json` | 输出格式（精简后仅 `json`） |
| `pageno` | int | 否 | `1` | 页码（≥1） |
| `language` | string | 否 | `auto` | 语言代码。`zh-CN`=中文, `en`=英文, `auto`=自动, `all`=全部 |
| `safesearch` | int | 否 | `0` | 安全搜索：`0`=关闭, `1`=中等, `2`=严格 |
| `time_range` | string | 否 | — | 时间范围：`day`, `week`, `month`, `year` |
| `categories` | string | 否 | `general` | 搜索类别，逗号分隔。如 `general,images,news` |
| `engines` | string | 否 | — | 指定搜索引擎，逗号分隔。如 `google,duckduckgo` |
| `timeout_limit` | float | 否 | `3.0` | 单个引擎超时时间（秒） |

**响应：**
```
HTTP 200
Content-Type: application/json
```

**JSON 结构：**

```json
{
    "query": "python",
    "number_of_results": 0,
    "results": [
        {
            "url": "https://www.python.org/",
            "title": "Welcome to Python.org",
            "content": "The official home of the Python Programming Language...",
            "engine": "duckduckgo",
            "engines": ["duckduckgo", "google"],
            "parsed_url": ["https", "www.python.org", "/", "", "", ""],
            "template": "default.html",
            "img_src": "",
            "thumbnail": "",
            "score": 0.5,
            "category": "general",
            "publishedDate": null,
            "author": "",
            "metadata": "",
            "length": null,
            "positions": [1],
            "iframe_src": "",
            "audio_src": ""
        }
    ],
    "answers": [],
    "corrections": [],
    "infoboxes": [],
    "suggestions": ["python tutorial", "python download", "python documentation"],
    "unresponsive_engines": [
        ["google", "HTTP 429 Too Many Requests"]
    ]
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | string | 实际搜索词 |
| `number_of_results` | int | 结果总数（近似值） |
| `results` | array | 搜索结果列表 |
| `results[].url` | string | 结果链接 |
| `results[].title` | string | 标题 |
| `results[].content` | string | 内容摘要 |
| `results[].engine` | string | 主要来源引擎 |
| `results[].engines` | array | 所有贡献此结果的引擎 |
| `results[].score` | float | 相关性分数（0-1） |
| `results[].category` | string | 类别（general/images/news 等） |
| `results[].publishedDate` | string/null | 发布日期（ISO 8601） |
| `results[].parsed_url` | array | URL 各组成部分 |
| `results[].img_src` | string | 图片 URL（图片搜索时） |
| `results[].thumbnail` | string | 缩略图 URL |
| `results[].author` | string | 作者 |
| `results[].length` | string/null | 内容长度 |
| `answers` | array | 即时回答（如天气、计算、百科摘要） |
| `corrections` | array | 拼写纠正建议 |
| `infoboxes` | array | 信息框（百科摘要等） |
| `suggestions` | array | 搜索建议 |
| `unresponsive_engines` | array | 无响应的引擎列表 `[[引擎名, 错误信息]]` |

**错误响应：**

```json
// 400 — 缺少搜索词
{
    "error": "Missing query parameter 'q'"
}

// 500 — 搜索内部错误
{
    "error": "Search error: ..."
}
```

---

### 3. GET /config — 配置信息

获取当前 SearXNG 的配置信息，包括启用的引擎、类别等。

**请求：**
```
GET /config
```

**响应：**
```
HTTP 200
Content-Type: application/json
```

```json
{
    "categories": ["general", "images", "news", "videos", "music", "it", "science", "files", "social media"],
    "engines": [
        {
            "name": "duckduckgo",
            "categories": ["general"],
            "shortcut": "ddg",
            "disabled": false,
            "timeout": 3.0
        },
        {
            "name": "wikipedia",
            "categories": ["general", "science"],
            "shortcut": "wp",
            "disabled": false,
            "timeout": 3.0
        }
    ],
    "plugins": [],
    "instance_name": "SearXNG",
    "search": {
        "safe_search": 0,
        "default_lang": "",
        "formats": ["json"],
        "autocomplete": ""
    }
}
```

---

### 4. GET /stats — 统计信息

获取引擎使用统计和错误计数。

**请求：**
```
GET /stats?engine=all
```

**响应：**
```
HTTP 200
Content-Type: application/json
```

```json
{
    "engines": {
        "duckduckgo": {
            "total": 1523,
            "errors": 2,
            "success_rate": 99.87
        },
        "wikipedia": {
            "total": 890,
            "errors": 0,
            "success_rate": 100.0
        }
    }
}
```

---

## 搜索类别

SearXNG 将搜索引擎按类别分组。常用类别：

| 类别 | 说明 | 包含引擎示例 |
|------|------|-------------|
| `general` | 通用网页搜索 | DuckDuckGo, Brave, Google（需API Key） |
| `images` | 图片搜索 | Google Images, Bing Images |
| `news` | 新闻搜索 | Google News, Bing News |
| `videos` | 视频搜索 | YouTube, Dailymotion |
| `science` | 学术搜索 | Wikipedia, ArXiv, PubMed |
| `files` | 文件搜索 | 种子/文件搜索 |
| `social media` | 社交媒体 | Reddit, Twitter |
| `it` | 技术类 | GitHub, StackOverflow |
| `music` | 音乐搜索 | SoundCloud, Bandcamp |

---

## 默认可用引擎（无需 API Key）

以下引擎在默认配置下即可使用，无需额外申请 API Key：

| 引擎名 | 类别 | 说明 |
|--------|------|------|
| `duckduckgo` | general | DuckDuckGo 搜索 |
| `brave` | general | Brave Search |
| `wikipedia` | general, science | 维基百科 |
| `bing` | general | Bing（无需 Key，但可能被限） |
| `yahoo` | general, news | Yahoo 搜索 |
| `qwant` | general, news | Qwant 搜索 |
| `startpage` | general | Startpage（Google 匿名代理） |
| `arxiv` | science | 学术论文 |
| `github` | it | GitHub 仓库搜索 |
| `stackoverflow` | it | StackOverflow |
| `reddit` | social media | Reddit |

**注意：** 部分引擎（如 Google）需要 API Key，在 `searx/settings.yml` 中配置。

---

## Python Engine 调用示例

### 基础搜索

```python
import httpx

async def search(query: str, num: int = 10) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://127.0.0.1:8888/search",
            params={
                "q": query,
                "format": "json",
                "language": "zh-CN",
                "safesearch": 1,
                "categories": "general",
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["results"][:num]
```

### 指定引擎搜索

```python
response = await client.get(
    "http://127.0.0.1:8888/search",
    params={
        "q": "machine learning",
        "format": "json",
        "engines": "duckduckgo,wikipedia",
        "language": "en",
    }
)
```

### 时间范围搜索

```python
# 搜索最近一周的新闻
response = await client.get(
    "http://127.0.0.1:8888/search",
    params={
        "q": "AI news",
        "format": "json",
        "categories": "news",
        "time_range": "week",
    }
)
```

### 健康检查

```python
response = await client.get("http://127.0.0.1:8888/healthz")
assert response.text == "OK"
```

---

## 集成到 Python Engine

```python
# engine/src/search/searxng_provider.py

class SearXNGProvider(SearchProvider):
    def __init__(self, base_url: str = "http://127.0.0.1:8888"):
        self.base_url = base_url

    async def search(
        self,
        query: str,
        num: int = 10,
        language: str = "zh-CN",
        categories: str = "general",
        time_range: str | None = None,
    ) -> list[SearchResult]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "language": language,
                    "categories": categories,
                    "time_range": time_range,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            return [
                SearchResult(
                    url=r["url"],
                    title=r["title"],
                    snippet=r["content"],
                    engine=r["engine"],
                    score=r.get("score", 0),
                )
                for r in data["results"][:num]
            ]
```

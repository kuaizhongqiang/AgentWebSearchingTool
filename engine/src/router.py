# SPDX-License-Identifier: MIT
"""FastAPI router — main entry point for the engine.

Manages SearXNG subprocess lifecycle during app startup/shutdown.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from .config import load_config
from .search import SearchResult
from .search.searxng_provider import SearXNGProvider
from .fetch import FetchEngine
from .extract import ExtractEngine
from .retrieval import Document, ScoredDocument, DashScopeEmbedding, LMStudioEmbedding
from .retrieval.pipeline import CrossEncoder, RetrievalPipeline
from .searxng_runner import SearXNGManager

logger = logging.getLogger(__name__)

config = load_config()

# ── SearXNG subprocess manager ────────────────────────────────────────
searxng_config = config.get("searxng_core", {})
searxng_manager = SearXNGManager(
    port=searxng_config.get("port", 8888),
    bind_address=searxng_config.get("bind_address", "127.0.0.1"),
    searxng_secret=searxng_config.get("secret"),
    settings_path=searxng_config.get("settings_path"),
    core_path=searxng_config.get("path"),
    proxies=searxng_config.get("proxies"),
)

search_provider = SearXNGProvider(
    searxng_url=searxng_manager.searxng_url,
)
fetch_engine = FetchEngine(
    request_interval=config["fetch"]["request_interval"],
    max_concurrent=config["fetch"]["max_concurrent"],
)
extract_engine = ExtractEngine(max_content_length=config["extract"]["max_content_length"])

# Retrieval pipeline (lazy init)
_retrieval_pipeline: RetrievalPipeline | None = None


def _get_retrieval_pipeline() -> RetrievalPipeline:
    global _retrieval_pipeline
    if _retrieval_pipeline is not None:
        return _retrieval_pipeline

    rc = config["retrieval"]
    emb_cfg = rc["embedding"]
    if emb_cfg["provider"] == "lmstudio":
        embedder = LMStudioEmbedding(
            base_url=emb_cfg["lmstudio"]["base_url"],
            model=emb_cfg["lmstudio"].get("model", ""),
        )
    else:
        embedder = DashScopeEmbedding(
            api_key=emb_cfg["dashscope"].get("api_key", ""),
            model=emb_cfg["dashscope"]["model"],
        )

    cross_encoder = CrossEncoder(model_name=rc["cross_encoder"]["model"])
    _retrieval_pipeline = RetrievalPipeline(
        embedder=embedder,
        cross_encoder=cross_encoder,
        top_k_coarse=rc.get("top_k_coarse"),
        top_k_final=rc["top_k"],
    )
    return _retrieval_pipeline


class SearchRequest(BaseModel):
    query: str
    num: int = 10
    engine: str = "google"
    page: int = 1


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    unresponsive_engines: list[str] = []
    page: int = 1


class FetchRequest(BaseModel):
    url: str
    extract: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class FetchResponse(BaseModel):
    url: str
    status_code: int = 0
    title: str = ""
    text: str = ""
    fetched_with: str = ""


class ScrapeRequest(BaseModel):
    urls: list[str]
    extract: bool = True


class ScrapeResponse(BaseModel):
    results: list[FetchResponse]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start SearXNG on startup, shut it down on shutdown."""
    # ── Startup ──
    auto_start = config.get("searxng_core", {}).get("auto_start", True)
    if auto_start:
        try:
            searxng_manager.start()
        except RuntimeError as e:
            logger.error("Failed to start SearXNG: %s", e)
            logger.warning("Engine will start without SearXNG — search endpoints will fail")
    else:
        logger.info(
            "SearXNG auto-start disabled — ensure SearXNG is running at %s",
            searxng_manager.searxng_url,
        )

    yield

    # ── Shutdown ──
    logger.info("Engine shutting down — stopping SearXNG")
    if auto_start:
        searxng_manager.stop()
    await fetch_engine.close()


app = FastAPI(title="AgentWebSearchingTool Engine", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    searxng_status = "ok" if searxng_manager.is_ready else "unavailable"
    return {
        "status": "ok",
        "searxng": searxng_status,
        "searxng_url": searxng_manager.searxng_url,
    }


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if not searxng_manager.is_ready:
        raise HTTPException(status_code=503, detail="SearXNG is not ready")
    try:
        response = await search_provider.search(query=req.query, num=req.num, engine=req.engine, page=req.page)
        return SearchResponse(query=response.query, results=response.results,
                              unresponsive_engines=response.unresponsive_engines, page=response.page)
    except Exception as e:
        logger.error("Search failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/fetch", response_model=FetchResponse)
async def fetch(req: FetchRequest):
    try:
        page = await fetch_engine.fetch(req.url)
        if req.extract and page.html:
            extracted = extract_engine.extract(page.html, url=page.url)
            return FetchResponse(url=page.url, status_code=page.status_code,
                                 title=extracted.title, text=extracted.text,
                                 fetched_with=page.fetched_with)
        return FetchResponse(url=page.url, status_code=page.status_code, fetched_with=page.fetched_with)
    except Exception as e:
        logger.error("Fetch failed for %s: %s", req.url, e)
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(req: ScrapeRequest):
    pages = await fetch_engine.fetch_many(req.urls)
    results = []
    for page in pages:
        if req.extract and page.html:
            extracted = extract_engine.extract(page.html, url=page.url)
            results.append(FetchResponse(url=page.url, status_code=page.status_code,
                                         title=extracted.title, text=extracted.text,
                                         fetched_with=page.fetched_with))
        else:
            results.append(FetchResponse(url=page.url, status_code=page.status_code, fetched_with=page.fetched_with))
    return ScrapeResponse(results=results)


class FilterRequest(BaseModel):
    query: str
    documents: list[str]
    top_k: int = 0  # 0 = use config default


class FilterResponse(BaseModel):
    query: str
    results: list[ScoredDocument]


@app.post("/filter", response_model=FilterResponse)
async def filter(req: FilterRequest):
    """Vector-based relevance filtering of documents against a query."""
    try:
        pipeline = _get_retrieval_pipeline()
        docs = [Document(text=t) for t in req.documents]
        top_k = req.top_k if req.top_k > 0 else config["retrieval"]["top_k"]
        pipeline.top_k_final = top_k
        results = pipeline.run(query=req.query, documents=docs)
        return FilterResponse(query=req.query, results=results)
    except Exception as e:
        logger.error("Filter failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


def main():
    import uvicorn
    uvicorn.run("src.router:app", host=config["server"]["host"], port=config["server"]["port"], reload=True)


if __name__ == "__main__":
    main()

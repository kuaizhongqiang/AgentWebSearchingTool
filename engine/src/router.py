# SPDX-License-Identifier: MIT
"""FastAPI router — main entry point for the engine.

Endpoints:
  POST /search   — execute search via SearXNG
  POST /fetch    — fetch and extract a single page
  POST /scrape   — batch fetch and extract multiple pages
  GET  /health   — health check
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from .config import load_config
from .search import SearchResult
from .search.searxng_provider import SearXNGProvider
from .fetch import FetchEngine, PageContent
from .extract import ExtractEngine, ExtractedContent

logger = logging.getLogger(__name__)

# ── Global state ────────────────────────────────────────────────────────────

config = load_config()
search_provider = SearXNGProvider(searxng_url=config["search"]["searxng_url"])
fetch_engine = FetchEngine(
    request_interval=config["fetch"]["request_interval"],
    max_concurrent=config["fetch"]["max_concurrent"],
)
extract_engine = ExtractEngine(max_content_length=config["extract"]["max_content_length"])


# ── Request/Response models ─────────────────────────────────────────────────

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


# ── App lifecycle ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Engine starting — SearXNG at %s", config["search"]["searxng_url"])
    yield
    logger.info("Engine shutting down")


app = FastAPI(title="AgentWebSearchingTool Engine", version="0.1.0", lifespan=lifespan)


# ── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    """Execute a search via the configured search provider."""
    try:
        response = await search_provider.search(
            query=req.query,
            num=req.num,
            engine=req.engine,
            page=req.page,
        )
        return SearchResponse(
            query=response.query,
            results=response.results,
            unresponsive_engines=response.unresponsive_engines,
            page=response.page,
        )
    except Exception as e:
        logger.error("Search failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/fetch", response_model=FetchResponse)
async def fetch(req: FetchRequest):
    """Fetch a single page and optionally extract its content."""
    try:
        page = await fetch_engine.fetch(req.url)
        if req.extract and page.html:
            extracted = extract_engine.extract(page.html, url=page.url)
            return FetchResponse(
                url=page.url,
                status_code=page.status_code,
                title=extracted.title,
                text=extracted.text,
                fetched_with=page.fetched_with,
            )
        return FetchResponse(
            url=page.url,
            status_code=page.status_code,
            fetched_with=page.fetched_with,
        )
    except Exception as e:
        logger.error("Fetch failed for %s: %s", req.url, e)
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(req: ScrapeRequest):
    """Batch fetch and extract multiple pages."""
    pages = await fetch_engine.fetch_many(req.urls)
    results = []
    for page in pages:
        if req.extract and page.html:
            extracted = extract_engine.extract(page.html, url=page.url)
            results.append(
                FetchResponse(
                    url=page.url,
                    status_code=page.status_code,
                    title=extracted.title,
                    text=extracted.text,
                    fetched_with=page.fetched_with,
                )
            )
        else:
            results.append(
                FetchResponse(
                    url=page.url,
                    status_code=page.status_code,
                    fetched_with=page.fetched_with,
                )
            )
    return ScrapeResponse(results=results)


# ── Entry point ─────────────────────────────────────────────────────────────

def main():
    """Run the engine server via uvicorn."""
    import uvicorn
    uvicorn.run(
        "src.router:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=True,
    )


if __name__ == "__main__":
    main()

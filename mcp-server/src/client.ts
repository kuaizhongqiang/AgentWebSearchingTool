import type { SearchResult } from "./tools/search.js";

export interface EngineConfig {
  baseUrl: string;
  timeout: number;
}

export class EngineClient {
  private baseUrl: string;
  private timeout: number;

  constructor(config?: Partial<EngineConfig>) {
    this.baseUrl = config?.baseUrl ?? "http://127.0.0.1:8000";
    this.timeout = config?.timeout ?? 30000;
  }

  async search(query: string, options?: { num?: number; engine?: string; page?: number }): Promise<{
    results: SearchResult[];
    unresponsive_engines: string[];
  }> {
    const resp = await fetch(`${this.baseUrl}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        num: options?.num ?? 10,
        engine: options?.engine ?? "google",
        page: options?.page ?? 1,
      }),
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Engine search failed (${resp.status}): ${text}`);
    }
    return resp.json();
  }

  async fetch(url: string, extract?: boolean): Promise<{
    url: string;
    status_code: number;
    title?: string;
    text?: string;
    fetched_with?: string;
  }> {
    const resp = await fetch(`${this.baseUrl}/fetch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, extract: extract ?? true }),
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Engine fetch failed (${resp.status}): ${text}`);
    }
    return resp.json();
  }

  async scrape(urls: string[], extract?: boolean): Promise<{
    results: Array<{
      url: string;
      status_code: number;
      title?: string;
      text?: string;
      fetched_with?: string;
    }>;
  }> {
    const resp = await fetch(`${this.baseUrl}/scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls, extract: extract ?? true }),
      signal: AbortSignal.timeout(this.timeout * 2),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Engine scrape failed (${resp.status}): ${text}`);
    }
    return resp.json();
  }

  async filter(query: string, documents: string[], topK?: number): Promise<{
    query: string;
    results: Array<{ document: { text: string; metadata: Record<string, unknown> }; score: number }>;
  }> {
    const resp = await fetch(`${this.baseUrl}/filter`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, documents, top_k: topK ?? 0 }),
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Engine filter failed (${resp.status}): ${text}`);
    }
    return resp.json();
  }
}

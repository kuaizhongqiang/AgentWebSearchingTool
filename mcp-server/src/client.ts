import type { SearchResult, FetchResult, FilterItem } from "@agent-web-search/types";

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
    return this._post("/search", {
      query,
      num: options?.num ?? 10,
      engine: options?.engine ?? "google",
      page: options?.page ?? 1,
    });
  }

  async fetch(url: string, extract?: boolean): Promise<FetchResult> {
    return this._post("/fetch", { url, extract: extract ?? true });
  }

  async scrape(urls: string[], extract?: boolean): Promise<{ results: FetchResult[] }> {
    return this._post("/scrape", { urls, extract: extract ?? true });
  }

  async filter(query: string, documents: string[], topK?: number): Promise<{
    query: string;
    results: Array<{ document: { text: string; metadata: Record<string, unknown> }; score: number }>;
  }> {
    return this._post("/filter", { query, documents, top_k: topK ?? 0 });
  }

  private async _post(path: string, body: unknown): Promise<any> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Engine ${path} failed (${resp.status}): ${text}`);
    }
    return resp.json();
  }
}

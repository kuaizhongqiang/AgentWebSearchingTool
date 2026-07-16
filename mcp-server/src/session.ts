import { randomUUID } from "node:crypto";
import type { SearchResult } from "@agent-web-search/types";

interface SessionEntry {
  results: SearchResult[];
  query: string;
  createdAt: number;
}

export class SessionManager {
  private sessions = new Map<string, SessionEntry>();
  private maxAge: number;

  constructor(maxAgeMs: number = 5 * 60 * 1000) {
    this.maxAge = maxAgeMs;
  }

  createSession(query: string, results: SearchResult[]): string {
    const sessionId = randomUUID();
    this.sessions.set(sessionId, { results, query, createdAt: Date.now() });
    this._evict();
    return sessionId;
  }

  getSession(sessionId: string): SessionEntry | undefined {
    const entry = this.sessions.get(sessionId);
    if (!entry) return undefined;
    if (Date.now() - entry.createdAt > this.maxAge) {
      this.sessions.delete(sessionId);
      return undefined;
    }
    return entry;
  }

  getPage(sessionId: string, page: number, pageSize: number = 10): { results: SearchResult[]; total: number } {
    const entry = this.getSession(sessionId);
    if (!entry) return { results: [], total: 0 };
    const start = (page - 1) * pageSize;
    const results = entry.results.slice(start, start + pageSize);
    return { results, total: entry.results.length };
  }

  private _evict(): void {
    const now = Date.now();
    for (const [id, entry] of this.sessions) {
      if (now - entry.createdAt > this.maxAge) {
        this.sessions.delete(id);
      }
    }
    // Hard limit
    if (this.sessions.size > 1000) {
      const sorted = [...this.sessions.entries()].sort((a, b) => a[1].createdAt - b[1].createdAt);
      const toDelete = sorted.slice(0, sorted.length - 1000);
      for (const [id] of toDelete) {
        this.sessions.delete(id);
      }
    }
  }
}

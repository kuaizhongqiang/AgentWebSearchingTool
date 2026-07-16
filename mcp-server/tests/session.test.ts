import { describe, it, expect } from "vitest";
import { SessionManager } from "../src/session.js";

describe("SessionManager", () => {
  it("creates and retrieves sessions", () => {
    const sm = new SessionManager(60000);
    const sid = sm.createSession("hello", [{ title: "Result", url: "https://x.com" }]);
    const entry = sm.getSession(sid);
    expect(entry).toBeDefined();
    expect(entry!.query).toBe("hello");
    expect(entry!.results).toHaveLength(1);
  });

  it("returns undefined for unknown session", () => {
    const sm = new SessionManager(60000);
    expect(sm.getSession("nonexistent")).toBeUndefined();
  });

  it("supports pagination", () => {
    const sm = new SessionManager(60000);
    const results = Array.from({ length: 25 }, (_, i) => ({
      title: `Result ${i + 1}`, url: `https://x.com/${i}`,
    }));
    const sid = sm.createSession("test", results);

    const page1 = sm.getPage(sid, 1, 10);
    expect(page1.results).toHaveLength(10);
    expect(page1.total).toBe(25);

    const page3 = sm.getPage(sid, 3, 10);
    expect(page3.results).toHaveLength(5);
  });

  it("expires old sessions", async () => {
    const sm = new SessionManager(10); // 10ms TTL
    const sid = sm.createSession("test", [{ title: "T", url: "https://x.com" }]);
    await new Promise(r => setTimeout(r, 20));
    expect(sm.getSession(sid)).toBeUndefined();
  });

  it("handles empty sessions gracefully", () => {
    const sm = new SessionManager(60000);
    const sid = sm.createSession("empty", []);
    const page = sm.getPage(sid, 1, 10);
    expect(page.results).toHaveLength(0);
    expect(page.total).toBe(0);
  });
});

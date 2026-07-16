import { describe, it, expect } from "vitest";
import { EngineClient } from "../src/client.js";

describe("EngineClient", () => {
  it("uses default base URL", () => {
    const client = new EngineClient();
    expect(client).toBeDefined();
  });

  it("accepts custom base URL", () => {
    const client = new EngineClient({ baseUrl: "http://localhost:9999" });
    expect(client).toBeDefined();
  });

  it("search throws on connection error", async () => {
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:1", timeout: 1000 });
    await expect(client.search("test")).rejects.toThrow();
  });

  it("fetch throws on connection error", async () => {
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:1", timeout: 1000 });
    await expect(client.fetch("https://example.com")).rejects.toThrow();
  });

  it("scrape throws on connection error", async () => {
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:1", timeout: 1000 });
    await expect(client.scrape(["https://example.com"])).rejects.toThrow();
  });

  it("filter throws on connection error", async () => {
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:1", timeout: 1000 });
    await expect(client.filter("test", ["doc"])).rejects.toThrow();
  });
});

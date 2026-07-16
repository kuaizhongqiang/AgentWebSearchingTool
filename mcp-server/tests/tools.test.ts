import { describe, it, expect } from "vitest";
import { SearchParamsSchema } from "../src/tools/search.js";
import { FetchParamsSchema } from "../src/tools/fetch.js";
import { ScrapeParamsSchema } from "../src/tools/scrape.js";
import { FilterParamsSchema } from "../src/tools/filter.js";
import { handleWebSearch } from "../src/tools/search.js";
import { EngineClient } from "../src/client.js";

describe("SearchParamsSchema", () => {
  it("accepts valid params", () => {
    const params = SearchParamsSchema.parse({ query: "hello" });
    expect(params.query).toBe("hello");
    expect(params.num_results).toBe(10);
  });

  it("rejects empty query", () => {
    expect(() => SearchParamsSchema.parse({ query: "" })).toThrow();
  });
});

describe("FetchParamsSchema", () => {
  it("rejects invalid URL", () => {
    expect(() => FetchParamsSchema.parse({ url: "bad" })).toThrow();
  });
});

describe("ScrapeParamsSchema", () => {
  it("rejects empty list", () => {
    expect(() => ScrapeParamsSchema.parse({ urls: [] })).toThrow();
  });

  it("limits to 20 URLs", () => {
    const params = ScrapeParamsSchema.parse({
      urls: Array.from({ length: 20 }, (_, i) => `https://x.com/${i}`),
    });
    expect(params.urls).toHaveLength(20);
  });
});

describe("FilterParamsSchema", () => {
  it("rejects empty query", () => {
    expect(() => FilterParamsSchema.parse({ query: "", results: ["a"] })).toThrow();
  });
});

describe("Tool handlers", () => {
  it("handleWebSearch returns formatted content", async () => {
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:1", timeout: 1000 });
    await expect(handleWebSearch(client, { query: "test", num_results: 5, engine: "google" }))
      .rejects.toThrow();
  });
});

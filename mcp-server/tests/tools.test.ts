import { describe, it, expect } from "vitest";
import { SearchParamsSchema } from "../src/tools/search.js";
import { FetchParamsSchema } from "../src/tools/fetch.js";
import { ScrapeParamsSchema } from "../src/tools/scrape.js";
import { FilterParamsSchema } from "../src/tools/filter.js";

describe("SearchParamsSchema", () => {
  it("accepts valid params", () => {
    const params = SearchParamsSchema.parse({ query: "hello" });
    expect(params.query).toBe("hello");
    expect(params.num_results).toBe(10);
  });

  it("rejects empty query", () => {
    expect(() => SearchParamsSchema.parse({ query: "" })).toThrow();
  });

  it("accepts custom num_results", () => {
    const params = SearchParamsSchema.parse({ query: "test", num_results: 5 });
    expect(params.num_results).toBe(5);
  });
});

describe("FetchParamsSchema", () => {
  it("accepts valid URL", () => {
    const params = FetchParamsSchema.parse({ url: "https://example.com" });
    expect(params.url).toBe("https://example.com");
  });

  it("rejects invalid URL", () => {
    expect(() => FetchParamsSchema.parse({ url: "not-a-url" })).toThrow();
  });

  it("defaults extract_mode to true", () => {
    const params = FetchParamsSchema.parse({ url: "https://example.com" });
    expect(params.extract_mode).toBe(true);
  });
});

describe("ScrapeParamsSchema", () => {
  it("accepts valid URLs", () => {
    const params = ScrapeParamsSchema.parse({ urls: ["https://a.com", "https://b.com"] });
    expect(params.urls).toHaveLength(2);
  });

  it("rejects empty array", () => {
    expect(() => ScrapeParamsSchema.parse({ urls: [] })).toThrow();
  });

  it("rejects invalid URLs", () => {
    expect(() => ScrapeParamsSchema.parse({ urls: ["bad"] })).toThrow();
  });
});

describe("FilterParamsSchema", () => {
  it("accepts valid params", () => {
    const params = FilterParamsSchema.parse({ query: "test", results: ["a", "b"] });
    expect(params.query).toBe("test");
    expect(params.results).toHaveLength(2);
  });

  it("rejects empty query", () => {
    expect(() => FilterParamsSchema.parse({ query: "", results: ["a"] })).toThrow();
  });
});

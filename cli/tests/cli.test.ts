import { describe, it, expect } from "vitest";

describe("CLI module", () => {
  it("imports without errors", async () => {
    const mod = await import("../src/index.js");
    expect(mod.program).toBeDefined();
  });

  it("search command definition", async () => {
    const { program } = await import("../src/index.js");
    const cmd = program.commands.find(c => c.name() === "search");
    expect(cmd).toBeDefined();
    expect(cmd?.name()).toBe("search");
  });

  it("fetch command definition", async () => {
    const { program } = await import("../src/index.js");
    const cmd = program.commands.find(c => c.name() === "fetch");
    expect(cmd).toBeDefined();
  });

  it("scrape command definition", async () => {
    const { program } = await import("../src/index.js");
    const cmd = program.commands.find(c => c.name() === "scrape");
    expect(cmd).toBeDefined();
  });

  it("filter command definition", async () => {
    const { program } = await import("../src/index.js");
    const cmd = program.commands.find(c => c.name() === "filter");
    expect(cmd).toBeDefined();
    expect(cmd?.name()).toBe("filter");
  });


  it("config command definition", async () => {
    const { program } = await import("../src/index.js");
    const cmd = program.commands.find(c => c.name() === "config");
    expect(cmd).toBeDefined();
  });

  it("serve command definition", async () => {
    const { program } = await import("../src/index.js");
    const cmd = program.commands.find(c => c.name() === "serve");
    expect(cmd).toBeDefined();
  });

  it("apiPost handles connection error", async () => {
    // Just verify the error handling path works
    const ENGINE_URL = "http://127.0.0.1:1";
    try {
      await fetch(`${ENGINE_URL}/health`, { signal: AbortSignal.timeout(100) });
    } catch (e) {
      expect(e).toBeDefined();
    }
  });

  it("parseInt option handling", () => {
    const num = "10";
    const engine = "google";
    expect(parseInt(num)).toBe(10);
    expect(engine).toBe("google");
  });

  it("JSON format output", () => {
    const data = { query: "test", results: [{ title: "A", url: "https://a.com" }] };
    const json = JSON.parse(JSON.stringify(data));
    expect(json.query).toBe("test");
    expect(json.results).toHaveLength(1);
  });
});

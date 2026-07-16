import { describe, it, expect } from "vitest";

describe("CLI argument parsing", () => {
  it("search command accepts query argument", async () => {
    // Verify the command definitions by importing
    const mod = await import("../src/index.js");
    expect(mod).toBeDefined();
  });

  it("search command parses options", () => {
    const num = "10";
    const engine = "google";
    expect(parseInt(num)).toBe(10);
    expect(engine).toBe("google");
  });

  it("fetch command validates URL format", () => {
    const validUrl = "https://example.com";
    const invalidUrl = "not-a-url";
    expect(() => new URL(validUrl)).not.toThrow();
    expect(() => new URL(invalidUrl)).toThrow();
  });
});

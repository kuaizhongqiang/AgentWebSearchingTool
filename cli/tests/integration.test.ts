import { describe, it, expect } from "vitest";
import { execFileSync, type ExecFileSyncOptions } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DIR = path.dirname(fileURLToPath(import.meta.url));
const CLI_PATH = path.resolve(DIR, "..", "dist", "index.js");

function runCLI(args: string[]): string {
  const opts: ExecFileSyncOptions = { encoding: "utf-8", timeout: 10000 };
  return execFileSync(process.execPath, [CLI_PATH, ...args], opts).toString();
}

describe("CLI", () => {
  it("config command shows engine URL", () => {
    const output = runCLI(["config"]);
    expect(output).toContain("Engine URL:");
    expect(output).toContain("Node.js:");
  });

  it("help output shows all commands", () => {
    const output = runCLI(["--help"]);
    expect(output).toContain("search");
    expect(output).toContain("fetch");
    expect(output).toContain("scrape");
    expect(output).toContain("filter");
    expect(output).toContain("config");
    expect(output).toContain("serve");
  });

  it("version output", () => {
    const output = runCLI(["--version"]);
    expect(output).toContain("0.1.0");
  });
});

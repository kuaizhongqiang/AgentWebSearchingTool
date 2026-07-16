#!/usr/bin/env node

import { createInterface } from "node:readline";
import { Command } from "commander";
import type { SearchResult, FetchResult, FilterItem } from "@agent-web-search/types";

const ENGINE_URL = process.env.ENGINE_URL ?? "http://127.0.0.1:8000";

async function apiPost(path: string, body: unknown): Promise<unknown> {
  const resp = await fetch(`${ENGINE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API error (${resp.status}): ${text}`);
  }
  return resp.json();
}

const program = new Command();

program
  .name("awst")
  .description("Agent Web Searching Tool CLI")
  .version("0.1.0");

// ── search ─────────────────────────────────────────────────────────────

program
  .command("search")
  .description("Search the web")
  .argument("<query>", "Search query")
  .option("-n, --num <number>", "Number of results", "10")
  .option("-e, --engine <engine>", "Search engine", "google")
  .option("--fetch", "Also fetch page content for each result")
  .option("--filter", "Apply vector filter to results")
  .option("-f, --format <format>", "Output format (text|json)", "text")
  .action(async (query, options) => {
    try {
      const data = await apiPost("/search", {
        query, num: parseInt(options.num), engine: options.engine,
      }) as { results: SearchResult[] };
      let results = data.results;

      if (options.fetch) {
        console.error(`Fetching ${results.length} pages...`);
        const scrapeData = await apiPost("/scrape", {
          urls: results.map(r => r.url), extract: true,
        }) as { results: FetchResult[] };
        results = results.map((r, i) => ({ ...r, content: scrapeData.results[i]?.text ?? r.content }));
      }

      if (options.filter) {
        console.error("Filtering results...");
        const filterData = await apiPost("/filter", {
          query, documents: results.map(r => r.content || r.title), top_k: 5,
        }) as { results: FilterItem[] };
        const keepTexts = new Set(filterData.results.map(r => r.text));
        results = results.filter(r => keepTexts.has(r.content || r.title));
      }

      if (options.format === "json") {
        console.log(JSON.stringify({ query, results }, null, 2));
      } else {
        for (const r of results) {
          console.log(`\n  [${r.score?.toFixed(2) ?? "?"}] ${r.title}`);
          console.log(`       ${r.url}`);
          if (r.content) console.log(`       ${r.content.slice(0, 200)}...`);
        }
        console.log(`\n--- ${results.length} results ---`);
      }
    } catch (error) {
      console.error("Search failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// ── fetch ──────────────────────────────────────────────────────────────

program
  .command("fetch")
  .description("Fetch a single web page")
  .argument("<url>", "URL to fetch")
  .option("-f, --format <format>", "Output format (text|json)", "text")
  .action(async (url, options) => {
    try {
      const data = await apiPost("/fetch", { url, extract: true }) as FetchResult;
      if (options.format === "json") {
        console.log(JSON.stringify(data, null, 2));
      } else {
        console.log(`\n  Title: ${data.title ?? "(no title)"}`);
        console.log(`  URL:   ${data.url}`);
        console.log(`  Status: ${data.status_code}`);
        if (data.text) {
          process.stdout.write(`\n${data.text.slice(0, 2000)}`);
          if (data.text.length > 2000) process.stdout.write("\n... (truncated)");
        }
        console.log();
      }
    } catch (error) {
      console.error("Fetch failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// ── scrape ─────────────────────────────────────────────────────────────

program
  .command("scrape")
  .description("Batch fetch multiple pages")
  .argument("<urls...>", "URLs to scrape")
  .option("-f, --format <format>", "Output format (text|json)", "text")
  .action(async (urls, options) => {
    try {
      const data = await apiPost("/scrape", { urls, extract: true }) as { results: FetchResult[] };
      if (options.format === "json") {
        console.log(JSON.stringify(data, null, 2));
      } else {
        for (const r of data.results) {
          console.log(`\n== ${r.url} (${r.status_code}) ==`);
          console.log(`   Title: ${r.title ?? ""}`);
          if (r.text) {
            process.stdout.write(r.text.slice(0, 500));
            if (r.text.length > 500) process.stdout.write("...");
          }
        }
        console.log(`\n--- ${data.results.length} pages scraped ---`);
      }
    } catch (error) {
      console.error("Scrape failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// ── filter (独立命令 + 管道) ───────────────────────────────────────────

program
  .command("filter")
  .description("Filter documents using vector similarity (supports stdin pipe)")
  .requiredOption("-q, --query <query>", "Query to filter by")
  .option("-f, --format <format>", "Output format (text|json)", "text")
  .argument("[documents...]", "Documents to filter (omit to read from stdin)")
  .action(async (documents, options) => {
    try {
      let docs: string[] = documents;

      // Pipe mode: read documents from stdin
      if (!docs || docs.length === 0) {
        const rl = createInterface({ input: process.stdin });
        docs = [];
        for await (const line of rl) {
          const trimmed = line.trim();
          if (trimmed) docs.push(trimmed);
        }
      }

      if (docs.length === 0) {
        console.error("No documents provided. Pass as arguments or pipe via stdin.");
        process.exit(1);
      }

      const data = await apiPost("/filter", {
        query: options.query, documents: docs, top_k: 10,
      }) as { results: FilterItem[] };

      if (options.format === "json") {
        console.log(JSON.stringify(data, null, 2));
      } else {
        for (const r of data.results) {
          console.log(`  [${r.score.toFixed(3)}] ${r.text.slice(0, 200)}`);
        }
        console.log(`\n--- ${data.results.length} results ---`);
      }
    } catch (error) {
      console.error("Filter failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// ── config ─────────────────────────────────────────────────────────────

program
  .command("config")
  .description("Show current configuration")
  .action(() => {
    console.log(`Engine URL: ${ENGINE_URL}`);
    console.log(`Node.js: ${process.version}`);
  });

// ── serve ──────────────────────────────────────────────────────────────

program
  .command("serve")
  .description("Start MCP Server mode (stdio)")
  .action(() => {
    console.error("Starting MCP Server...");
    const MCP_SERVER_PATH = process.env.MCP_SERVER_PATH
      ?? "../mcp-server/dist/index.js";
    const child = require("child_process").spawn(
      process.execPath,
      [MCP_SERVER_PATH],
      { stdio: "inherit", env: { ...process.env, ENGINE_URL } }
    );
    child.on("exit", (code: number | null) => process.exit(code ?? 0));
  });

// ── parse ──────────────────────────────────────────────────────────────

const isDirectRun = process.argv[1]?.endsWith("index.ts") || process.argv[1]?.endsWith("index.js") || process.argv[1]?.includes("awst");
if (isDirectRun) {
  program.parse();
}

export { program };

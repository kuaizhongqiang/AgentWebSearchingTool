#!/usr/bin/env node

import { Command } from "commander";

const ENGINE_URL = process.env.ENGINE_URL ?? "http://127.0.0.1:8000";

interface SearchResult {
  title: string;
  url: string;
  content?: string;
  engine?: string;
  score?: number;
}

interface FetchResult {
  url: string;
  status_code: number;
  title?: string;
  text?: string;
}

interface FilterResult {
  text: string;
  score: number;
}

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
        query,
        num: parseInt(options.num),
        engine: options.engine,
      }) as { results: SearchResult[] };

      let results = data.results;

      // Fetch page content inline
      if (options.fetch) {
        console.error(`Fetching ${results.length} pages...`);
        const fetchResults = await apiPost("/scrape", {
          urls: results.map((r: SearchResult) => r.url),
          extract: true,
        }) as { results: FetchResult[] };
        results = results.map((r: SearchResult, i: number) => ({
          ...r,
          content: fetchResults.results[i]?.text ?? r.content,
        }));
      }

      // Apply vector filter
      if (options.filter) {
        console.error("Filtering results...");
        const filterData = await apiPost("/filter", {
          query,
          documents: results.map((r: SearchResult) => r.content || r.title),
          top_k: 5,
        }) as { results: FilterResult[] };
        const filteredTexts = new Set(filterData.results.map((r: FilterResult) => r.text));
        results = results.filter((r: SearchResult) => filteredTexts.has(r.content || r.title));
      }

      if (options.format === "json") {
        console.log(JSON.stringify({ query, results }, null, 2));
      } else {
        for (const r of results) {
          console.log(`\n  [${r.score?.toFixed(2) ?? "?"}] ${r.title}`);
          console.log(`       ${r.url}`);
          if (r.content) {
            console.log(`       ${r.content.slice(0, 200)}...`);
          }
        }
        console.log(`\n--- ${results.length} results ---`);
      }
    } catch (error) {
      console.error("Search failed:", error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

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

program
  .command("config")
  .description("Show current configuration")
  .action(() => {
    console.log(`Engine URL: ${ENGINE_URL}`);
    console.log(`Node.js: ${process.version}`);
  });

program
  .command("serve")
  .description("Start MCP Server mode (stdio)")
  .action(() => {
    console.error("Starting MCP Server...");
    // Redirect to the MCP Server binary
    import("child_process").then((cp) => {
      const child = cp.spawn("npx", ["@kuaizhongqiang/mcp-server-agent-web-search"], {
        stdio: "inherit",
        env: { ...process.env, ENGINE_URL },
      });
      child.on("exit", (code) => process.exit(code ?? 0));
    });
  });

// Only parse when run directly (not imported for tests)
const isDirectRun = process.argv[1]?.endsWith("index.ts") || process.argv[1]?.endsWith("index.js") || process.argv[1]?.includes("awst");
if (isDirectRun) {
  program.parse();
}

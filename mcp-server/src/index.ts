#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { EngineClient } from "./client.js";
import { SessionManager } from "./session.js";
import { SearchParamsSchema, handleWebSearch } from "./tools/search.js";
import { FetchParamsSchema, handleWebFetch } from "./tools/fetch.js";
import { ScrapeParamsSchema, handleWebScrape } from "./tools/scrape.js";
import { FilterParamsSchema, handleSearchFilter } from "./tools/filter.js";

const ENGINE_URL = process.env.ENGINE_URL ?? "http://127.0.0.1:8000";
const client = new EngineClient({ baseUrl: ENGINE_URL });
const sessions = new SessionManager();

const server = new Server(
  { name: "agent-web-search-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "web_search",
      description: "Search the web — returns session_id for pagination",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query" },
          num_results: { type: "number", default: 10, description: "Number of results" },
          engine: { type: "string", default: "google", description: "Search engine" },
        },
        required: ["query"],
      },
    },
    {
      name: "web_search_page",
      description: "Get a page of previously cached search results",
      inputSchema: {
        type: "object",
        properties: {
          session_id: { type: "string", description: "Session ID from web_search" },
          page: { type: "number", description: "Page number (1-based)", default: 1 },
          page_size: { type: "number", default: 10, description: "Results per page" },
        },
        required: ["session_id"],
      },
    },
    {
      name: "web_fetch",
      description: "Fetch a single web page and extract its content",
      inputSchema: {
        type: "object",
        properties: {
          url: { type: "string", description: "URL to fetch" },
          extract_mode: { type: "boolean", default: true, description: "Extract main content" },
        },
        required: ["url"],
      },
    },
    {
      name: "web_scrape",
      description: "Batch fetch and extract multiple web pages",
      inputSchema: {
        type: "object",
        properties: {
          urls: { type: "array", items: { type: "string" }, description: "URLs to scrape" },
          extract_mode: { type: "boolean", default: true, description: "Extract main content" },
        },
        required: ["urls"],
      },
    },
    {
      name: "search_filter",
      description: "Filter/search documents using vector similarity against a query",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Query to filter by" },
          results: { type: "array", items: { type: "string" }, description: "Documents to filter" },
          top_k: { type: "number", description: "Top K results" },
        },
        required: ["query", "results"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "web_search": {
        const params = SearchParamsSchema.parse(args);
        const result = await handleWebSearch(client, params);
        // Cache results in session and attach session_id
        const body = JSON.parse(result.content[0].text);
        const sessionId = sessions.createSession(params.query, body.results);
        result.content[0].text = JSON.stringify({ ...body, session_id: sessionId }, null, 2);
        return result;
      }
      case "web_search_page": {
        const { session_id, page = 1, page_size = 10 } = args as any;
        const pageResult = sessions.getPage(session_id, page, page_size);
        return {
          content: [{ type: "text" as const, text: JSON.stringify(pageResult, null, 2) }],
        };
      }
      case "web_fetch": {
        const params = FetchParamsSchema.parse(args);
        return await handleWebFetch(client, params);
      }
      case "web_scrape": {
        const params = ScrapeParamsSchema.parse(args);
        return await handleWebScrape(client, params);
      }
      case "search_filter": {
        const params = FilterParamsSchema.parse(args);
        return await handleSearchFilter(client, params);
      }
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Tool ${name} failed: ${message}`);
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`MCP Server started — Engine URL: ${ENGINE_URL}`);
}

main().catch((error) => {
  console.error("MCP Server fatal error:", error);
  process.exit(1);
});

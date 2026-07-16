import { describe, it, expect, beforeAll, afterAll } from "vitest";
import http from "node:http";
import { spawn, type ChildProcess } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DIR = path.dirname(fileURLToPath(import.meta.url));

let mockEngine: http.Server;
let enginePort: number;
let mcpProcess: ChildProcess;

function startMockEngine(port: number): Promise<void> {
  return new Promise((resolve) => {
    mockEngine = http.createServer((req, res) => {
      res.setHeader("Content-Type", "application/json");

      if (req.url === "/search" && req.method === "POST") {
        let body = "";
        req.on("data", (c) => (body += c));
        req.on("end", () => {
          const { query } = JSON.parse(body);
          res.end(JSON.stringify({
            query,
            results: [
              { title: "Result 1", url: "https://example.com/1", score: 0.95 },
              { title: "Result 2", url: "https://example.com/2", score: 0.85 },
            ],
            unresponsive_engines: [],
          }));
        });
      } else if (req.url === "/fetch" && req.method === "POST") {
        res.end(JSON.stringify({
          url: "https://example.com", status_code: 200,
          title: "Test Page", text: "Hello World",
        }));
      } else if (req.url === "/health" && req.method === "GET") {
        res.end(JSON.stringify({ status: "ok" }));
      } else {
        res.statusCode = 404;
        res.end(JSON.stringify({ error: "not found" }));
      }
    });
    mockEngine.listen(port, resolve);
  });
}

describe("MCP Server integration", () => {
  beforeAll(async () => {
    enginePort = 18989;
    await startMockEngine(enginePort);

    const serverPath = path.resolve(DIR, "..", "dist", "index.js");
    mcpProcess = spawn(process.execPath, [serverPath], {
      env: { ...process.env, ENGINE_URL: `http://127.0.0.1:${enginePort}` },
      stdio: ["pipe", "pipe", "pipe"],
    });
  }, 15000);

  afterAll(() => {
    mcpProcess?.kill();
    mockEngine?.close();
  });

  it("responds to JSON-RPC initialize", async () => {
    const msg = JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize", params: {
      protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "test", version: "1" },
    } }) + "\n";

    const response = await sendMCP(msg);
    expect(response).toBeDefined();
    expect(response.id).toBe(1);
  }, 10000);

  it("lists tools", async () => {
    const msg = JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }) + "\n";
    const response = await sendMCP(msg);

    expect(response).toBeDefined();
    expect(response.result).toBeDefined();
    const tools = response.result.tools.map((t: any) => t.name);
    expect(tools).toContain("web_search");
    expect(tools).toContain("web_fetch");
    expect(tools).toContain("web_scrape");
    expect(tools).toContain("search_filter");
    expect(tools).toContain("web_search_page");
  }, 10000);

  it("executes web_search tool", async () => {
    const msg = JSON.stringify({
      jsonrpc: "2.0", id: 3, method: "tools/call", params: {
        name: "web_search", arguments: { query: "hello", num_results: 5 },
      },
    }) + "\n";

    const response = await sendMCP(msg);
    expect(response).toBeDefined();
    expect(response.result).toBeDefined();
    const text = response.result.content[0].text;
    const data = JSON.parse(text);
    expect(data.query).toBe("hello");
    expect(data.results).toHaveLength(2);
    expect(data.session_id).toBeDefined();
  }, 10000);

  it("executes web_search_page with session_id", async () => {
    // First do a search to get session_id
    const searchMsg = JSON.stringify({
      jsonrpc: "2.0", id: 4, method: "tools/call", params: {
        name: "web_search", arguments: { query: "page-test" },
      },
    }) + "\n";
    const searchResp = await sendMCP(searchMsg);
    const searchData = JSON.parse(searchResp.result.content[0].text);
    const sessionId = searchData.session_id;

    // Then get page
    const pageMsg = JSON.stringify({
      jsonrpc: "2.0", id: 5, method: "tools/call", params: {
        name: "web_search_page", arguments: { session_id: sessionId, page: 1, page_size: 10 },
      },
    }) + "\n";
    const pageResp = await sendMCP(pageMsg);
    const pageData = JSON.parse(pageResp.result.content[0].text);
    expect(pageData.results).toHaveLength(2);
    expect(pageData.total).toBe(2);
  }, 10000);

  it("executes web_fetch tool", async () => {
    const msg = JSON.stringify({
      jsonrpc: "2.0", id: 6, method: "tools/call", params: {
        name: "web_fetch", arguments: { url: "https://example.com" },
      },
    }) + "\n";

    const response = await sendMCP(msg);
    expect(response).toBeDefined();
    const text = response.result.content[0].text;
    const data = JSON.parse(text);
    expect(data.status_code).toBe(200);
    expect(data.title).toBe("Test Page");
  }, 10000);

  it("rejects invalid params", async () => {
    const msg = JSON.stringify({
      jsonrpc: "2.0", id: 7, method: "tools/call", params: {
        name: "web_search", arguments: { query: "" },
      },
    }) + "\n";

    const response = await sendMCP(msg);
    expect(response.error).toBeDefined();
  }, 10000);
});

function sendMCP(msg: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("MCP response timeout")), 8000);

    const onData = (data: Buffer) => {
      clearTimeout(timeout);
      mcpProcess.stdout?.removeListener("data", onData);
      try {
        // Handle MCP JSON-RPC with Content-Length headers
        const text = data.toString();
        // Strip headers if present (MCP uses HTTP-like headers)
        const jsonStr = text.includes("\r\n\r\n") ? text.split("\r\n\r\n")[1] : text;
        const lines = jsonStr.trim().split("\n");
        for (const line of lines) {
          if (!line) continue;
          try {
            resolve(JSON.parse(line));
            return;
          } catch {}
        }
        reject(new Error(`Can't parse MCP response: ${text.slice(0, 200)}`));
      } catch (e) {
        reject(e);
      }
    };

    mcpProcess.stdout!.on("data", onData);
    mcpProcess.stdin!.write(msg);
  });
}

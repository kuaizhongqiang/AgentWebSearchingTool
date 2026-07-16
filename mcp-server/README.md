# MCP Server — Agent Web Search

MCP Server providing web search, fetch, scrape, and vector filter tools for AI agents.

## Quick Start

```bash
npm install
npm run build

# Ensure the Python Engine is running on port 8000
ENGINE_URL=http://127.0.0.1:8000 node dist/index.js
```

## MCP Configuration

Add to your MCP client config (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "web-search": {
      "command": "node",
      "args": ["path/to/mcp-server/dist/index.js"],
      "env": {
        "ENGINE_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search web, returns `session_id` for pagination |
| `web_search_page` | Get paginated results from a previous search |
| `web_fetch` | Fetch and extract a single page |
| `web_scrape` | Batch fetch multiple pages |
| `search_filter` | Vector similarity filter documents |

## Session Management

Search results are cached for 5 minutes. Use `session_id` from `web_search`
response to paginate with `web_search_page`.

## Env Variables

- `ENGINE_URL` — Python Engine URL (default: `http://127.0.0.1:8000`)

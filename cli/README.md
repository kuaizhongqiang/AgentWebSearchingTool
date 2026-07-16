# CLI — Agent Web Search (awst)

Command-line interface for the Agent Web Searching Tool engine.

## Installation

```bash
npm install -g agent-web-search-cli
```

Or run locally:

```bash
npm install
npm run build
npm link   # makes `awst` available globally
```

## Usage

```bash
# Search
awst search "python programming" --num 5 --engine google
awst search "news" --fetch                    # auto-fetch pages
awst search "test" --filter                   # apply vector filter
awst search "hello" -f json                   # JSON output

# Fetch a page
awst fetch https://example.com

# Batch scrape
awst scrape https://a.com https://b.com

# Vector filter (also supports stdin pipe)
awst filter --query "python" "doc1 text" "doc2 text"
echo -e "doc1\ndoc2" | awst filter --query "python"

# Configuration
awst config

# Start MCP Server mode
awst serve
```

## Pipe Mode

```bash
# Pipe search results into filter
awst search "machine learning" -f json | jq '.results[].content' | awst filter --query "deep learning"
```

## Env Variables

- `ENGINE_URL` — Python Engine URL (default: `http://127.0.0.1:8000`)
- `MCP_SERVER_PATH` — Path to MCP Server binary (default: `../mcp-server/dist/index.js`)

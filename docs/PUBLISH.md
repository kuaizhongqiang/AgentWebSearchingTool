# Package 发布方案

## 概述

Monorepo 多包发布策略。Python 包发布到 PyPI，TypeScript 包发布到 npm。全自动化：GitHub Release → CI 自动 publish。

## 包清单

| 包目录 | 包名 | 注册表 | 语言 | 说明 |
|--------|------|--------|------|------|
| `engine/` | `agent-web-search-engine` | PyPI | Python | 核心引擎 |
| `mcp-server/` | `@kuaizhongqiang/mcp-server-agent-web-search` | npm | TypeScript | MCP Server |
| `cli/` | `agent-web-search-cli` | npm | TypeScript | CLI 工具 |

> `searxng-core/` 作为 package-data **打包进** `agent-web-search-engine` 的 wheel 中，随 PyPI 一起发布。
> engine 启动时自动以子进程启动 SearXNG，无需用户额外部署。

---

## 版本策略

所有包**统一版本号**，与 GitHub Release Tag 对齐。

- Tag `v0.1.0` → 所有包版本 `0.1.0`
- semantic-release 自动计算版本号
- 变更日志统一在根 CHANGELOG.md

---

## CI/CD 工作流

### 1. 主 CI (`ci.yml`) — PR 检查

```
PR → main
  ├─ commitlint (Conventional Commits)
  ├─ engine: ruff lint + pytest
  ├─ mcp-server: tsc --noEmit + npm test
  └─ cli: tsc --noEmit + npm test
```

### 2. Release (`release.yml`) — 自动 Tag + Publish

触发：push 到 main 分支（且 CI 通过）

```
push to main
  │
  ▼
semantic-release 分析提交历史
  │
  ├─ feat: → bump minor
  ├─ fix:  → bump patch
  └─ BREAKING CHANGE → bump major
  │
  ▼
git tag vX.Y.Z
GitHub Release 创建
CHANGELOG.md 更新
  │
  ├─→ PyPI publish (engine/)
  ├─→ npm publish (mcp-server/)
  └─→ npm publish (cli/)
```

---

## 工作流文件

### `.github/workflows/release.yml`

```yaml
name: Release & Publish

on:
  push:
    branches: [main]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  # ── 1. 版本计算 & GitHub Release ──
  release:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.semantic.outputs.version }}
      released: ${{ steps.semantic.outputs.new_release_published }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Semantic Release
        id: semantic
        run: |
          npm install -g semantic-release \
            @semantic-release/commit-analyzer \
            @semantic-release/release-notes-generator \
            @semantic-release/changelog \
            @semantic-release/github \
            @semantic-release/git
          npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # ── 2. PyPI Publish ──
  pypi-publish:
    needs: release
    if: needs.release.outputs.released == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: engine
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive         # ← 需要拉取 searxng-core submodule
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Bundle searxng-core       # ← 将 submodule 内容复制到包内
        run: python scripts/prepare_build.py
      - name: Build
        run: |
          pip install build
          python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: engine/dist/
          password: ${{ secrets.PYPI_API_TOKEN }}

  # ── 3. npm Publish (mcp-server) ──
  npm-publish-mcp:
    needs: release
    if: needs.release.outputs.released == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: mcp-server
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: "https://registry.npmjs.org"
      - name: Set version
        run: npm version ${{ needs.release.outputs.version }} --no-git-tag-version
      - run: npm ci
      - run: npm run build
      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}

  # ── 4. npm Publish (cli) ──
  npm-publish-cli:
    needs: release
    if: needs.release.outputs.released == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: cli
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: "https://registry.npmjs.org"
      - name: Set version
        run: npm version ${{ needs.release.outputs.version }} --no-git-tag-version
      - run: npm ci
      - run: npm run build
      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## Secrets 配置

在 GitHub Repository Settings → Secrets and variables → Actions 中添加：

| Secret 名 | 值 | 说明 |
|-----------|-----|------|
| `PYPI_API_TOKEN` | `pypi-xxxx` | PyPI API Token（在 pypi.org → Account → API tokens 创建） |
| `NPM_TOKEN` | `npm_xxxx` | npm Access Token（在 npmjs.com → Access Tokens 创建，选 Automation 类型） |
| `GITHUB_TOKEN` | 自动提供 | GitHub 自动注入，无需手动配置 |

---

## 包配置文件

### `engine/pyproject.toml`

> 注意下文的依赖列表是简化版，实际以 `engine/pyproject.toml` 为准。

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "agent-web-search-engine"
version = "0.0.0"  # CI 自动更新
description = "AI Agent web search & intelligent filtering engine"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
]
dependencies = [
    "fastapi>=0.100",
    "uvicorn>=0.23",
    "httpx>=0.25",
    "trafilatura>=1.6",
    "playwright>=1.40",
    "sentence-transformers>=2.2",
    "dashscope>=1.14",
    "openai>=1.0",
    "numpy>=1.24",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "ruff>=0.1",
]

[project.scripts]
agent-web-search-engine = "src.router:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### `mcp-server/package.json`

```json
{
  "name": "@kuaizhongqiang/mcp-server-agent-web-search",
  "version": "0.0.0",
  "description": "MCP Server for Agent Web Searching Tool",
  "license": "MIT",
  "type": "module",
  "main": "dist/index.js",
  "bin": {
    "agent-web-search-mcp": "dist/index.js"
  },
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vitest": "^1.0.0",
    "@types/node": "^20.0.0"
  }
}
```

### `cli/package.json`

```json
{
  "name": "agent-web-search-cli",
  "version": "0.0.0",
  "description": "CLI tool for Agent Web Searching Tool",
  "license": "MIT",
  "type": "module",
  "main": "dist/index.js",
  "bin": {
    "awst": "dist/index.js"
  },
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "commander": "^12.0.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vitest": "^1.0.0",
    "@types/node": "^20.0.0"
  }
}
```

---

## `.releaserc.json`

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/changelog",
      { "changelogFile": "CHANGELOG.md" }
    ],
    [
      "@semantic-release/github",
      { "assets": [] }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["CHANGELOG.md"],
        "message": "chore(release): ${nextRelease.version}\n\n${nextRelease.notes}"
      }
    ]
  ],
  "ignorePaths": ["searxng-core/**"]
}
```

---

## 发布流程（开发者视角）

1. 写代码，提交遵循 Conventional Commits：
   ```
   feat: 添加 Cross-encoder 精排
   fix: 修复搜索结果去重逻辑
   ```

2. 提 PR → CI 跑 lint + test + typecheck

3. PR 合并到 main → CI 自动：
   - 分析提交 → 计算版本号
   - 创建 git tag
   - 创建 GitHub Release
   - engine/ → PyPI
   - mcp-server/ → npm
   - cli/ → npm

4. 用户安装：
   ```bash
   pip install agent-web-search-engine
   npm install -g agent-web-search-cli
   # 或 MCP 配置中引用
   npx @kuaizhongqiang/mcp-server-agent-web-search
   ```

---

## 初始设置步骤（首次）

```bash
# 1. PyPI 创建 API Token
# https://pypi.org/manage/account/token/
# Scope: agent-web-search-engine

# 2. npm 创建 Access Token
# https://www.npmjs.com/settings/kuaizhongqiang/tokens
# Type: Automation

# 3. GitHub Secrets
gh secret set PYPI_API_TOKEN --repo kuaizhongqiang/AgentWebSearchingTool
gh secret set NPM_TOKEN --repo kuaizhongqiang/AgentWebSearchingTool

# 4. 首次手动发布（v0.1.0）
# CI 会在第一次合并 feat: 提交时自动发布
```

# CI / CD

## 自动 Tag 策略

全自动，无需手动操作。基于 Conventional Commits 语义化版本：

| 提交类型 | 版本变更 | 示例 |
|---------|---------|------|
| `fix:` | patch (0.1.0 → 0.1.1) | `fix: 修复搜索结果去重逻辑` |
| `feat:` | minor (0.1.0 → 0.2.0) | `feat: 添加 Cross-encoder 精排` |
| `feat!:` / `BREAKING CHANGE:` | major (0.1.0 → 1.0.0) | `feat!: 重构 Provider 接口` |

合并到 `main` 时 CI 自动：
1. 计算新版本号（基于提交历史）
2. 打 git tag
3. 创建 GitHub Release
4. 生成 Changelog

## 工作流文件

### `.github/workflows/ci.yml` — 主 CI

触发条件：所有 PR 和 main 分支 push。

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # ── Python Engine ──
  python-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: engine
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest --cov

  python-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: engine
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff
      - run: ruff check src/

  # ── MCP Server ──
  mcp-typecheck:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: mcp-server
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx tsc --noEmit

  mcp-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: mcp-server
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test

  # ── CLI ──
  cli-typecheck:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: cli
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx tsc --noEmit

  cli-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: cli
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test

  # ── Commitlint ──
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: wagoid/commitlint-github-action@v6
```

### `.github/workflows/release.yml` — 自动 Tag + Release

触发条件：push 到 main 分支（仅 CI 通过后）。

```yaml
name: Auto Release

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    # 只在 CI 全部通过后执行（用 workflow_run 或合并到一个文件）
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      # 安装 semantic-release 全家桶
      - run: npm install -g semantic-release @semantic-release/commit-analyzer @semantic-release/release-notes-generator @semantic-release/changelog @semantic-release/github @semantic-release/git @semantic-release/exec

      - name: Run semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npx semantic-release
```

### `.releaserc.json` — semantic-release 配置

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/github",
      {
        "assets": []
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["CHANGELOG.md"],
        "message": "chore(release): ${nextRelease.version}\n\n${nextRelease.notes}"
      }
    ]
  ]
}
```

### `commitlint.config.js`

```js
module.exports = {
  extends: ["@commitlint/config-conventional"],
};
```

## 发布流程示意

```
PR merged → main
  │
  ▼
CI 全部通过
  │
  ▼
semantic-release 分析提交历史
  │
  ├─ fix: 开头 → bump patch → v0.1.1
  ├─ feat: 开头 → bump minor → v0.2.0
  └─ BREAKING CHANGE → bump major → v1.0.0
  │
  ▼
自动: git tag vX.Y.Z
自动: GitHub Release + Changelog
自动: 推送 tag 到远程
```

## 注意事项

- 永远不要手动 `git tag`，让 CI 全自动管理
- 合并 PR 时使用 Squash Merge，commit message 遵循 Conventional Commits
- 如果某次合并不想触发 release，在 commit 里加 `[skip release]`
- `searxng-core/` 目录的变更不触发 release（通过 `.releaserc.json` 的 ignorePaths 排除）

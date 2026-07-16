# SearXNG-core 清理方案

## 目标

将 SearXNG fork 从"带 Web UI 的完整搜索引擎"精简为"纯 JSON API 的搜索服务"，移除所有不必要的文件和目录。

## 清理原则

1. **只保留搜索 API 能力** — 去掉 Web UI、前端、多语言
2. **去掉容器化** — 不使用 Docker，裸机 Python 运行
3. **保留核心引擎** — 搜索引擎适配器、结果聚合、JSON API
4. **最小化依赖** — 删除开发工具链（Go/Node/lint）
5. **保留上游同步能力** — 不破坏 git 历史，方便定期 merge 上游

## 清理清单

### 一、顶层：可删除的目录和文件

```bash
# 删除整个目录
rm -rf .github/          # GitHub CI/Issue 模板（12文件）
rm -rf .devcontainer/    # VS Code DevContainer
rm -rf .helix/           # Helix 编辑器配置
rm -rf docs/             # Sphinx 文档（~204文件）
rm -rf tests/            # 测试代码（~52文件）
rm -rf utils/            # Shell 构建工具脚本（18文件）
rm -rf searxng_extra/    # 数据更新维护脚本（14文件）
rm -rf client/           # 前端 Simple Theme 源码（~75文件）
rm -rf container/        # Docker 构建文件（6文件）

# 删除 searx/ 中的 Web UI 相关
rm -rf searx/static/     # 编译后的前端静态文件（~30文件）
rm -rf searx/templates/  # Jinja2 HTML 模板（~71文件）
rm -rf searx/translations/ # 多语言翻译（~241文件）

# 删除顶层多余文件
rm -f go.mod go.sum          # Go 开发工具
rm -f package.json .nvmrc    # Node 开发工具
rm -f babel.cfg .weblate     # 国际化工具
rm -f .pylintrc .yamllint.yml pyrightconfig.json .coveragerc  # Lint 配置
rm -f mise.toml .editorconfig # 工具版本管理
rm -f AI_POLICY.rst AUTHORS.rst CHANGELOG.rst CONTRIBUTING.rst
rm -f SECURITY.md PULL_REQUEST_TEMPLATE.md
rm -f requirements-dev.txt   # 开发依赖
rm -f .dockerignore
```

### 二、searx/ 内部：可精简的文件

```bash
# 多语言/国际化相关（纯 API 不需要）
rm -f searx/babel_extract.py
rm -f searx/locales.py
rm -f searx/sxng_locales.py

# 可选功能模块
rm -f searx/external_bang.py    # !bang 跳转（搜索引擎跳转）
rm -f searx/weather.py          # 天气模块
rm -f searx/wikidata_units.py   # Wikidata 单位

# 前端相关
rm -rf searx/favicons/          # 网站图标（API 不需要，可保留用于结果中显示引擎图标）
rm -rf searx/infopage/          # 多语言信息页面（19文件）

# 缓存（可选，初期不需要 Valkey/Redis）
# 如果不用缓存，可以删除：
# rm -f searx/valkeydb.py searx/valkeylib.py
```

**注意：`searx/favicons/` 和 `searx/infopage/` 可根据需要保留。** 建议先保留，后续按需删除。

### 三、必须保留的核心文件

```
searx/                        # 核心源码（必保）
├── __init__.py
├── _settings.py
├── autocomplete.py           # 搜索建议
├── botdetection/             # 反爬虫（保护引擎不被封）
├── brand.py                  # 品牌信息（可简化）
├── cache.py                  # 缓存
├── compat.py                 # 兼容性
├── data/                     # 引擎依赖的静态数据（~7MB，必须保留）
├── enginelib/                # 引擎基类
├── engines/                  # ~250 个搜索引擎实现（核心！）
├── exceptions.py
├── extended_types.py
├── external_urls.py
├── flaskfix.py
├── limiter.py + limiter.toml # 请求限流
├── metrics/                  # 指标（可选但建议保留）
├── network/                  # HTTP 网络层
├── openmetrics.py
├── plugins/                  # 插件系统（引擎可能依赖）
├── preferences.py            # 偏好设置
├── query.py                  # 查询处理
├── results.py                # 结果处理
├── result_types/             # 结果类型定义
├── search/                   # 搜索核心流程
├── searxng.msg               # 消息定义
├── settings.yml              # 主配置（86KB，重要）
├── settings_defaults.py      # 默认设置
├── settings_loader.py        # 设置加载
├── sqlitedb.py               # SQLite（引擎缓存用）
├── utils.py                  # 工具函数
├── version.py                # 版本
├── webadapter.py             # Web 适配层
├── webapp.py                 # Flask Web 应用（51KB）
├── webutils.py               # Web 工具
└── answerers/                # 即时回答（可选保留）

# 顶层必保
requirements.txt              # Python 依赖
requirements-server.txt       # 服务器依赖
setup.py                      # 包安装
manage                        # 管理脚本
LICENSE                       # AGPL-3.0 许可证
README.rst                    # 项目说明
```

### 四、setup.py 需要修改

删除 Web UI 相关目录后，`setup.py` 中的 `package_data` 需要移除以下引用：

```python
# 删除这些行：
# 'static/**',
# 'templates/**',
# 'translations/**',
# 'infopage/**',
```

同时 `install_requires` 中可移除：
- `babel`, `flask-babel` — 国际化
- `jinja2` — 模板引擎（如果纯 JSON API 不渲染 HTML）
- `pygments` — 代码高亮
- `whitenoise` — 静态文件服务

### 五、requirements.txt 精简

保留核心依赖：
```
certifi          - SSL 证书
flask            - Web 框架 ★
lxml             - XML/HTML 解析 ★
pyyaml           - YAML 配置 ★
httpx[http2]     - HTTP 客户端 ★
httpx-socks      - SOCKS 代理
sniffio          - 异步检测
markdown-it-py   - Markdown 解析
msgspec          - 序列化
typer            - CLI
isodate          - 日期解析
python-dateutil  - 日期处理
typing-extensions- 类型扩展
```

移除：
```
babel, flask-babel  - 国际化
jinja2              - 模板引擎（纯 API 不需要）
pygments            - 代码高亮
whitenoise          - 静态文件
valkey              - 缓存（可选）
```

### 六、settings.yml 精简

`searx/settings.yml` (86KB) 是全局配置。需要修改的关键项：

```yaml
# 搜索设置
search:
  safe_search: 0          # 0=关闭
  autocomplete: ""        # 关闭自动补全（不需要前端）
  default_lang: ""        # 空=自动检测
  formats:
    - json                # 只保留 json
    # - html              # 删除
    # - csv               # 删除（可选保留）
    # - rss               # 删除

# 服务设置
server:
  secret_key: "change-me" # 改为随机字符串
  bind_address: "127.0.0.1"  # 只监听本地
  port: 8888
  limiter: false          # 内部服务不需要限流
  image_proxy: false      # 不需要图片代理
  method: "GET"           # 只允许 GET（内部 API 安全）

# UI 设置（全部关闭/删除）
ui:
  static_use_hash: false
  default_theme: simple
  # 删除 themes, default_locale 等

# 插件（精简）
enabled_plugins: []       # 不需要前端插件

# 输出格式
outgoing:
  useragent_suffix: ""
```

### 七、清理后的目录结构

```
searxng-core/
├── LICENSE
├── README.rst
├── manage                    # 管理脚本
├── requirements.txt          # 精简后的依赖
├── requirements-server.txt
├── setup.py                  # 修改后的安装配置
└── searx/
    ├── __init__.py
    ├── settings.yml          # 精简后的配置
    ├── settings_defaults.py
    ├── settings_loader.py
    ├── webapp.py             # Flask 入口
    ├── webadapter.py
    ├── webutils.py
    ├── search/               # 搜索流程
    ├── engines/              # ~250 搜索引擎
    ├── enginelib/            # 引擎基类
    ├── network/              # HTTP 网络层
    ├── plugins/              # 插件
    ├── botdetection/         # 反爬虫
    ├── data/                 # 静态数据
    ├── result_types/         # 结果类型
    ├── answerers/            # 即时回答
    ├── metrics/              # 指标
    ├── limiter.py
    ├── limiter.toml
    ├── preferences.py
    ├── query.py
    ├── results.py
    ├── cache.py
    ├── sqlitedb.py
    ├── autocomplete.py
    ├── external_urls.py
    ├── brand.py
    ├── compat.py
    ├── exceptions.py
    ├── extended_types.py
    ├── flaskfix.py
    ├── utils.py
    ├── version.py
    ├── openmetrics.py
    └── searxng.msg
```

### 八、启动方式

清理后，启动 SearXNG-core：

```bash
cd searxng-core
python -m venv .venv
source .venv/bin/activate
pip install -e .
searxng-run    # 启动服务，监听 127.0.0.1:8888
```

或者直接：
```bash
python -m searx.webapp
```

### 九、验证清理结果

```bash
# 健康检查
curl http://127.0.0.1:8888/healthz
# 预期: OK

# JSON 搜索
curl "http://127.0.0.1:8888/search?q=python&format=json"
# 预期: JSON 搜索结果
```

### 十、注意事项

1. **`searx/engines/` 中的引擎并非全部可用** — 部分需要 API Key（如 Google、Bing），在 `settings.yml` 中配置
2. **默认引擎已禁用需要 API Key 的** — SearXNG 默认只启用无需认证的引擎（DuckDuckGo、Wikipedia 等）
3. **`searx/data/` 目录不可删除** — 包含引擎运行所需的静态数据（货币代码、语言列表等）
4. **上游同步时注意冲突** — 清理后的目录结构与原仓库差异大，merge 上游时可能有冲突，需要手动处理
5. **部分模块删除可能影响引擎** — 如 `searx/favicons/` 被某些引擎引用，建议先保留，后续逐步排查

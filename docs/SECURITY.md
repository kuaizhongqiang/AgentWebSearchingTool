# SearXNG-core 安全审查报告

## 审查范围

对 `searxng-core/` (fork 自 searxng/searxng) 进行全量安全审查，覆盖网络外联、数据泄露、代码执行、隐私风险。

## 总体结论

SearXNG 在设计上是**注重隐私**的元搜索引擎，**未发现遥测/电话回家/用户跟踪代码**。所有网络外联行为均为功能性（向搜索引擎发送查询、自动补全、获取公开数据）。在部署到私人服务器前，需处理以下发现的问题。

---

## 一、必须修复（部署前）

### 1. 🔴 默认 secret_key 硬编码

**位置：** `searx/settings.yml` L105

```yaml
secret_key: "ultrasecretkey"
```

**风险：** Flask session 签名密钥使用硬编码默认值。使用默认配置的实例可被伪造 session。

**修复：** 部署前替换为随机字符串：
```bash
openssl rand -hex 16
```

### 2. 🔴 .mcp.json 泄露真实 API Key

**位置：** `.mcp.json` L8

```json
"API_KEY": "cbk-148109bf7ebd"
```

**风险：** 真实 API Key 已提交到仓库，应立刻轮换并移除。

**修复：** 
- 立即在 memory.kuai-private.top 轮换此 Key
- 将 `.mcp.json` 加入 `.gitignore`，改用 `.mcp.example.json` 模板

### 3. 🔴 open_metrics 无密码保护

**位置：** `searx/settings.yml` L18

```yaml
enable_metrics: true
open_metrics:
  password: ""   # 空密码！
```

**风险：** 指标端点无认证，可能泄露引擎使用统计（虽不含用户查询内容）。

**修复：** 生产环境设密码或禁用 `enable_metrics: false`。

---

## 二、建议修复（降低风险）

### 4. 🟡 速率限制默认关闭

```yaml
limiter: false
```

**风险：** 无限制的搜索请求可能被滥用。

**修复：** 内部使用场景可保持关闭，但部署脚本应明确标注。

### 5. 🟡 command 引擎允许执行任意 Shell 命令

**位置：** `searx/engines/command.py`

**风险：** 管理员可配置 shell 命令，用户查询被插入命令中。

**缓解措施（已内置）：**
- 需要 `tokens` 才能激活
- 支持 `query_type: path`（路径白名单）和 `query_type: enum`（值白名单）
- 超时 4 秒

**建议：** 不使用 command 引擎，在 settings.yml 中保持 `disabled: true`。

### 6. 🟡 Google CSE CX 硬编码

**位置：** `searx/engines/google_cse.py` L43

```python
CX = "partner-pub-8993703457585266:4862972284"
```

**风险：** 这是 blackle.com 的 Google CSE ID，非我们所有。

**建议：** 不影响安全，但该引擎默认已禁用。

---

## 三、隐私相关（了解即可）

### 7. 🔵 自动补全向第三方发送部分查询

`searx/autocomplete.py` 中的自动补全功能会将用户的部分输入发送到 Google/Bing/Baidu 等。这是设计预期的行为，且默认关闭（`search.autocomplete: ""`）。

### 8. 🔵 Sogou 自动补全通过腾讯 CDN

Sogou 自动补全请求发送到 `sor.html5.qq.com`（腾讯服务器）。

### 9. 🔵 中国引擎默认全部禁用

百度、360、搜狗等中国搜索引擎默认 `disabled: true`，良好实践。

### 10. 🔵 搜索引擎预热请求

Baidu/360search 会先访问首页获取 cookies（正常反爬行为，非数据外传）。

---

## 四、已确认安全（无需处理）

| 检查项 | 结果 |
|--------|------|
| 遥测/电话回家 | ❌ 未发现 |
| 用户行为跟踪 | ❌ 未发现 |
| 远程日志上传 | ❌ 未发现（仅本地 logging） |
| Metrics 含用户查询 | ❌ 不包含（仅引擎调用统计） |
| 硬编码真实 API Key（引擎内） | ❌ 未发现（仅占位符 `""`） |
| 后门/隐藏功能 | ❌ 未发现 |
| 第三方依赖已知漏洞 | 未发现（版本较新） |
| `exec()` 运行时调用 | ❌ 未发现（仅构建时 babel 提取） |

---

## 五、M1 清理时的安全加固清单

在 M1 清理 SearXNG 时同步执行：

- [ ] 删除 command 引擎（`searx/engines/command.py`）
- [ ] 删除 tor_check 插件（`searx/plugins/tor_check.py`）
- [ ] 删除 tracker_patterns 外联（`searx/data/tracker_patterns.py` 中去掉 ClearURLs 远程下载）
- [ ] 关闭 `enable_metrics`
- [ ] 关闭 `limiter`（内部使用）
- [ ] 删除 image_proxy 相关代码
- [ ] 确保 `bind_address: 127.0.0.1`
- [ ] 确保 `public_instance: false`
- [ ] `.mcp.json` 加入 `.gitignore`，创建 `.mcp.example.json`

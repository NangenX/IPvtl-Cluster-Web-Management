# IPVTL Cluster Web Management

## this project all build by AI tools.

**📊 项目分析文档**: [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) - 全面的项目分析、优化建议和实施路线图

English version: [README_en.md](README_en.md)

这是一个最小化的 IPVTL 集群管理面板示例，基于 FastAPI 提供后端 API，前端使用简单的静态页面（位于 `frontend/index.html`）。

**主要功能**
- **集群发现**: 从配置文件 `servers/servers.json` 加载服务器列表。
- **状态轮询**: 后端的 `Poller` 周期性向各服务器的 `/status` 接口拉取状态并缓存结果。
- **状态查询 API**: 提供 `/api/servers` 与 `/api/servers/{id}/status` 等接口供前端或外部系统使用。
- **通道管理（重启）**: 提供 `/api/servers/{id}/channels/{channel_id}/restart` 接口，通过向目标服务器发送 stop/start 请求实现通道重启（实现位于 `app/services/manager.py`）。
- **静态管理界面**: `frontend/index.html` 提供简单的 UI，支持查看 CPU、通道状态、自动刷新与重启通道操作。

**代码结构（概要）**
- **`app/main.py`**: 应用入口，初始化 FastAPI、加载服务器配置并在启动时创建 `Poller` 实例。
- **`app/config.py`**: 全局配置（轮询间隔、并发、超时、服务器配置文件位置等），使用 Pydantic 管理设置。
- **`app/models.py`**: Pydantic 数据模型定义（`Server`, `ServerStatus`, `Channel`）。
- **`app/api/servers.py`**: REST API 路由实现，负责载入服务器列表、返回服务器列表与单服务器状态、以及通道重启的 POST 接口。
- **`app/services/poller.py`**: 轮询器实现，异步并发获取每台服务器的状态并缓存到内存中，提供 `get_status` 接口供 API 查询。
- **`app/services/manager.py`**: 通道控制实现，通过 HTTP 请求触发目标服务器通道的停止与启动以完成“重启”操作。
- **`servers/servers.json`**: 示例服务器配置文件，默认格式为服务器对象数组（包含 `id`, `name`, `host`, `port`）。
- **`frontend/index.html`**: 简单的前端页面，调用后端 API 展示服务器与通道状态，并触发重启操作。

**安装与运行（开发/测试）**
1. 创建并激活虚拟环境（可选）

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

2. 安装依赖

```powershell
pip install -r requirements.txt
```

3. 启动服务（示例使用 `uvicorn`）

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. 打开浏览器访问 `http://localhost:8000/` 查看管理面板。

**配置说明**
- 修改服务器列表: 编辑 `servers/servers.json`，每个条目示例：

```json
{
	"id": "1",
	"name": "Server 1",
	"host": "192.168.2.172",
	"port": 8888
}
```

- 调整参数: 可以通过环境变量覆盖 `app/config.py` 中的 Pydantic `Settings`（例如 `POLL_INTERVAL`、`POLL_CONCURRENCY` 等）。

**API 概览**
- `GET /api/servers` — 返回服务器列表（从 Poller 获取）。
- `GET /api/servers/{server_id}/status` — 返回指定服务器的最新缓存状态（由 `Poller` 提供），包含 CPU 与通道信息。
- `POST /api/servers/{server_id}/channels/{channel_id}/restart` — 对指定服务器的指定通道执行重启（先 stop 再 start）。**需要认证**（如果启用）。
- `POST /api/servers/reload` — 重新加载服务器配置文件，无需重启应用。**需要认证**（如果启用）。

**API 认证（可选）**

默认情况下，API 认证是关闭的，以保持向后兼容性。要启用 API Key 认证：

1. 设置环境变量启用认证：
```bash
export API_KEY_ENABLED=true
export API_KEY=your-secret-api-key-here
```

2. 在请求敏感操作时添加 `X-API-Key` 请求头：
```bash
# 重启通道示例
curl -X POST http://localhost:8000/api/servers/1/channels/1/restart \
  -H "X-API-Key: your-secret-api-key-here"

# 重新加载服务器配置示例
curl -X POST http://localhost:8000/api/servers/reload \
  -H "X-API-Key: your-secret-api-key-here"
```

3. 需要认证的端点：
   - `POST /api/servers/{server_id}/channels/{channel_id}/restart`
   - `POST /api/servers/reload`

如果认证失败，API 将返回 401 Unauthorized 错误。

**设计与实现要点**
- 使用 FastAPI 提供异步路由，结合 `httpx` 异步客户端实现对上游服务器的轮询与控制请求。
- `Poller` 使用并发信号量限制同时进行的请求数，避免对被管理服务器造成过高压力。
- 支持运行时重新加载服务器配置，无需重启应用（通过 `/api/servers/reload` 端点）。
- 实现了结构化日志系统，支持通过 `LOG_LEVEL` 环境变量控制日志级别。
- 可选的 API Key 认证机制保护敏感操作。
- 前端为最小示例，便于快速替换为更复杂的 SPA 或运维控制台。

**配置参数**

所有配置项可通过环境变量覆盖：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `POLL_INTERVAL` | 10 | 轮询间隔（秒） |
| `MAX_SERVERS` | 100 | 最大服务器数量 |
| `POLL_CONCURRENCY` | 10 | 并发轮询数 |
| `HTTPX_TIMEOUT_SECONDS` | 5 | HTTP 请求超时 |
| `RESTART_STOP_TIMEOUT_SECONDS` | 10 | 停止通道超时 |
| `RESTART_START_TIMEOUT_SECONDS` | 10 | 启动通道超时 |
| `RESTART_DELAY_SECONDS` | 0.5 | 重启间隔延迟 |
| `LOG_LEVEL` | info | 日志级别（debug/info/warning/error） |
| `API_KEY_ENABLED` | false | 是否启用 API 认证 |
| `API_KEY` | "" | API 密钥（启用认证时必需） |

**调试与开发建议**
- 日志: 已实现结构化日志系统，通过 `LOG_LEVEL` 环境变量控制详细程度。
- 健壮性: 已添加输入验证、错误处理和可选的 API 认证。生产环境建议限制 CORS 允许的来源。

**下一步（建议）**
- 将前端重构为 React/Vue 应用并增加更详细的图形化监控。
- 添加单元测试与集成测试覆盖关键逻辑（`Poller`、`manager`、API 路由）。
- 为历史数据添加持久化存储（如时序数据库）。
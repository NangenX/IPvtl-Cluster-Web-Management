# Copilot 使用说明（给 AI 编码代理的即时上手指南）

以下说明聚焦于使 AI 代理能快速、安全地在本仓库内改动。仅记录从代码可观察到的事实与约定。

## 1. 大图（必须先看）
- 后端：FastAPI 应用，入口在 [app/main.py](app/main.py)。路由由 `app.api.servers` 注册。
- 轮询服务：`Poller` 在启动时创建并保存在 `app.state.poller`（见 [app/main.py](app/main.py) 的 `startup_event`）。它并发轮询外部服务的 `/status` 接口并缓存 `ServerStatus`（实现见 [app/services/poller.py](app/services/poller.py)）。
- 管理操作：通道重启由 [app/services/manager.py](app/services/manager.py) 实现，使用 `httpx.AsyncClient` 发起控制请求。
- 前端：静态单页在 [frontend/index.html](frontend/index.html)，直接调用后端 API（`/api/servers`、`/api/servers/{id}/status`、重启接口）。

## 2. 如何运行（确切可复制命令）
- 仓库提供 `start.bat`：创建 venv、安装依赖并以 `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` 启动。直接运行 `start.bat` 即可在 Windows 上启动开发环境。
- 依赖写在 `requirements.txt`，运行脚本会自动安装。

## 3. 关键实现细节与易踩坑点
- Poller 与 API 读取 servers.json 的不一致：
  - `Poller` 在应用启动时读取 `servers/servers.json` 并缓存到内存（传入构造函数）。
  - API 端点（[app/api/servers.py](app/api/servers.py)）每次请求会重新从文件读取 `servers/servers.json`。
  - 后果：修改 `servers/servers.json` 后，API 会立即反映修改，但正在运行的 `Poller` 不会自动更新；若需动态生效必须重启应用或为 `Poller` 增加热更新逻辑。
- `/status` 返回格式期望：`cpu`（数字或数组）与 `channels`（数组，元素包含 `id`、可选 `name`、`status`/`state`）。前端处理兼容性逻辑（见 [frontend/index.html](frontend/index.html)）。
- `restart_channel` 的实现为先 `stop` 再 `start`（见 [app/services/manager.py](app/services/manager.py)），改变顺序或超时需谨慎测试目标设备行为。
- 日志为 `print()` 调试输出，仓库尚未引入结构化 `logging`。重构为 `logging` 时请确保等价的日志级别与内容。

## 4. 配置与运行时常量（可直接依赖）
- 配置在 [app/config.py](app/config.py)，使用 Pydantic `Settings`。常用键：
  - `POLL_INTERVAL`（轮询间隔秒）
  - `MAX_SERVERS`（轮询服务器上限）
  - `POLL_CONCURRENCY`（并发请求上限）
  - `HTTPX_TIMEOUT_SECONDS`, `RESTART_STOP_TIMEOUT_SECONDS`, `RESTART_START_TIMEOUT_SECONDS`
  - `SERVERS_CONFIG_PATH`（默认 `servers/servers.json`）

## 5. 代码改动建议（可靠、安全的做法）
- 修改轮询逻辑时：保留对 `Poller._statuses` 的写入语义（当前实现保证即使请求失败也会写入占位状态）。任何变更都应兼顾前端对缺失状态的处理。
- 若要实现运行时增删服务器：为 `Poller` 增加协程安全的修改接口，或在 API 修改后重建 `app.state.poller`（并正确关闭旧 `Poller`）。
- 添加新路由：在 `app/api` 下添加模块并在 `app/main.py` 注册 router，或将路由直接加入 `app/api/servers.py`。

## 6. 发现与测试
- 仓库当前没有自动化测试目录或测试脚本（未在 README 中发现测试指引）。如果增加单元/集成测试，建议优先覆盖 `Poller` 的并发与故障场景，以及 `manager.restart_channel` 的超时/错误路径。

------
如需我把上述要点合并到项目的 README、生成 TODO（例如：为 Poller 增加热更新）、或实现运行时服务器列表管理接口，我可以继续实现并提交补丁。请指出你想优先改进的部分或是否需要更详细示例。

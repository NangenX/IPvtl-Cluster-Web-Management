# IPvtl Cluster Web Management 项目骨架

## 目录结构

```
ipvtl-cluster-manager/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # Pydantic 配置
│   ├── models.py            # 数据模型
│   ├── api/
│   │   ├── __init__.py
│   │   └── servers.py       # API 路由
│   └── services/
│       ├── __init__.py
│       ├── poller.py        # 轮询服务
│       └── manager.py       # 通道管理服务
├── frontend/
│   └── index.html           # 前端单页应用
├── servers/
│   └── servers.json         # 服务器配置
├── requirements.txt
├── .env.example
└── README.md
```

## 快速启动

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置服务器列表
cp servers/servers.example.json servers/servers.json
# 编辑 servers.json 添加你的服务器

# 4. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. 访问
# API 文档: http://localhost:8000/docs
# 管理界面: http://localhost:8000
```

## API 端点

### 本系统 API
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/servers` | 获取所有服务器及状态 |
| GET | `/api/servers/{server_id}` | 获取单个服务器详情 |
| POST | `/api/servers/{server_id}/refresh` | 手动刷新服务器状态 |
| POST | `/api/servers/{server_id}/channels/{channel_id}/start` | 启动通道 |
| POST | `/api/servers/{server_id}/channels/{channel_id}/stop` | 停止通道 |
| POST | `/api/servers/{server_id}/channels/{channel_id}/restart` | 重启通道 |
| POST | `/api/servers/reload` | 重新加载服务器配置 |
| GET | `/health` | 健康检查端点 |

### 对接的 IPVTL API
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/status` | 获取服务器状态(CPU+通道) |
| GET | `/channel{id}?start` | 启动指定通道 |
| GET | `/channel{id}?stop` | 停止指定通道 |

# IPVTL Cluster Manager

> 🎯 基于 Docker 的轻量级集群管理工具

---

## 🚀 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 编辑服务器配置
vim servers/servers.json

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问服务
# 打开浏览器访问: http://localhost:8000
```

### 方式二：纯 Docker 命令

```bash
# 1. 构建镜像
docker build -t ipvtl-cluster-manager:latest .

# 2. 运行容器
docker run -d \
  --name ipvtl-manager \
  -p 8000:8000 \
  -v $(pwd)/servers/servers.json:/app/servers/servers.json:ro \
  --restart unless-stopped \
  ipvtl-cluster-manager:latest

# 3. 访问服务
# 打开浏览器访问: http://localhost:8000
```

---

## ✅ Docker 特性

| 特性 | 说明 |
|:------|:------|
| 🏗️ **多阶段构建** | 减小镜像体积，优化构建效率 |
| 🔒 **非 root 用户** | 遵循安全最佳实践 |
| 💚 **健康检查** | 自动检测服务状态 |
| 📦 **配置外挂** | 修改 `servers.json` 无需重建镜像 |
| ⚙️ **环境变量** | 支持运行时动态配置 |
| 🔄 **自动重启** | `unless-stopped` 重启策略 |

---

## 📁 项目结构

```
ipvtl-cluster-manager/
├── 📄 Dockerfile              # Docker 镜像构建文件
├── 📄 docker-compose.yml      # Docker Compose 编排文件
├── 📄 .dockerignore           # Docker 构建忽略文件
├── 📄 requirements.txt        # Python 依赖列表
│
├── 📂 app/                    # 应用主目录
│   ├── __init__.py
│   ├── main.py                # 应用入口
│   ├── config.py              # 配置管理
│   ├── models.py              # 数据模型
│   │
│   ├── 📂 api/                # API 接口
│   │   ├── __init__.py
│   │   └── servers.py         # 服务器 API
│   │
│   └── 📂 services/           # 业务服务
│       ├── __init__.py
│       ├── poller.py          # 轮询服务
│       └── manager.py         # 管理服务
│
├── 📂 frontend/               # 前端资源
│   └── index.html             # 主页面
│
└── 📂 servers/                # 服务器配置
    └── servers.json           # 服务器列表配置
```

---

## 📝 使用说明

1. **配置服务器列表**：编辑 `servers/servers.json` 文件
2. **启动服务**：使用 Docker Compose 或 Docker 命令启动
3. **访问界面**：浏览器访问 `http://localhost:8000`
4. **查看日志**：使用 `docker-compose logs -f` 实时查看

---

## 🛠️ 技术栈

- **后端**: Python + FastAPI
- **前端**: HTML + JavaScript
- **容器**: Docker + Docker Compose
- **部署**: 多阶段构建 + 健康检查

---

## 📄 License

MIT License

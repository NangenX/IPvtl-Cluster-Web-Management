"""FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.models import HealthResponse
from app.api.servers import router as servers_router
from app.services.poller import poller_service
from app.services.manager import manager_service

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await poller_service.start()
    await manager_service.start()
    yield
    # 关闭时
    logger.info("Shutting down...")
    await manager_service.stop()
    await poller_service.stop()

# 创建应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# 注册 API 路由
app.include_router(servers_router)

# 健康检查端点
@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        servers_count=len(poller_service._servers),
        poll_interval=settings.poll_interval
    )

# 挂载静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 前端入口
@app.get("/")
async def index():
    """返回前端页面"""
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

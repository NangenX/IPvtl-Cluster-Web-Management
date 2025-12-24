from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import json
from typing import List

from app.models import Server, ServerStatus
from app.config import settings
from app.services.poller import Poller
from app.services.manager import restart_channel

router = APIRouter()


def load_servers() -> List[Server]:
    path = settings.SERVERS_CONFIG_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Server(**s) for s in data]
    except Exception:
        return []


@router.get("/api/servers")
async def get_servers():
    servers = load_servers()
    return [s.dict() for s in servers]


@router.get("/api/servers/{server_id}/status")
async def get_server_status(request: Request, server_id: str):
    servers = load_servers()
    print(f"Loaded servers: {servers}")  # 添加调试日志
    server = next((s for s in servers if s.id == server_id), None)
    if not server:
        raise HTTPException(status_code=404, detail="server not found")

    # 获取全局的 Poller 实例，用于查询服务器状态
    poller: Poller = request.app.state.poller
    print(f"Poller: {poller}, Server: {server}")  # 添加调试日志
    
    # 使用服务器 ID 获取状态
    status = poller.get_status(server.id) if poller else None
    
    # 如果未能获取到状态，返回 404 错误
    if not status:
        raise HTTPException(status_code=404, detail="status not found")

    # 返回服务器状态的 JSON 响应
    return JSONResponse(content=status.dict())


@router.post("/api/servers/{server_id}/channels/{channel_id}/restart")
async def post_restart_channel(server_id: str, channel_id: str):
    servers = load_servers()
    server = next((s for s in servers if s.id == server_id), None)
    if not server:
        raise HTTPException(status_code=404, detail="server not found")
    result = await restart_channel(server, channel_id)
    return JSONResponse(content=result)

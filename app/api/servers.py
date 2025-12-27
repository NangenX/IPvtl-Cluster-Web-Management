"""服务器管理 API 路由"""
from fastapi import APIRouter, HTTPException, Path
from app.models import ServerResponse, ChannelActionResult
from app.services.poller import poller_service
from app.services.manager import manager_service

router = APIRouter(prefix="/api/servers", tags=["servers"])

@router.get("", response_model=list[ServerResponse])
async def get_all_servers():
    """获取所有服务器及其状态"""
    servers = poller_service.get_all_servers()
    return [
        ServerResponse(config=config, state=state)
        for config, state in servers
    ]

@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(server_id: str):
    """获取单个服务器详情"""
    result = poller_service.get_server(server_id)
    if not result:
        raise HTTPException(status_code=404, detail="Server not found")
    config, state = result
    return ServerResponse(config=config, state=state)

@router.post("/{server_id}/refresh", response_model=ServerResponse)
async def refresh_server(server_id: str):
    """手动刷新服务器状态"""
    result = poller_service.get_server(server_id)
    if not result:
        raise HTTPException(status_code=404, detail="Server not found")
    state = await poller_service.poll_server(server_id)
    config, _ = result
    return ServerResponse(config=config, state=state)

@router.post(
    "/{server_id}/channels/{channel_id}/restart",
    response_model=ChannelActionResult
)
async def restart_channel(
    server_id: str,
    channel_id: int = Path(..., ge=1, description="通道编号 (从1开始)")
):
    """重启指定通道"""
    result = await manager_service.restart_channel(server_id, channel_id)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    return result

@router.post(
    "/{server_id}/channels/{channel_id}/stop",
    response_model=ChannelActionResult
)
async def stop_channel(
    server_id: str,
    channel_id: int = Path(..., ge=1, description="通道编号 (从1开始)")
):
    """停止指定通道"""
    result = await manager_service.stop_channel(server_id, channel_id)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    return result

@router.post(
    "/{server_id}/channels/{channel_id}/start",
    response_model=ChannelActionResult
)
async def start_channel(
    server_id: str,
    channel_id: int = Path(..., ge=1, description="通道编号 (从1开始)")
):
    """启动指定通道"""
    result = await manager_service.start_channel(server_id, channel_id)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    return result

@router.post("/reload")
async def reload_config():
    """重新加载服务器配置"""
    poller_service.reload_servers()
    count = len(poller_service._servers)
    return {"message": "Configuration reloaded", "count": count}

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import json
import re
from typing import List

from app.config import settings
from app.logging_config import get_logger
from app.models import Server, ServerStatus
from app.security import verify_api_key
from app.services.poller import Poller
from app.services.manager import restart_channel

router = APIRouter()
logger = get_logger(__name__)


def load_servers() -> List[Server]:
    """
    Load servers from configuration file.
    
    Note: This is kept for backward compatibility and initial loading.
    For runtime operations, prefer getting servers from the Poller instance.
    """
    path = settings.SERVERS_CONFIG_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Server(**s) for s in data]
    except Exception as e:
        logger.error(f"Failed to load servers from {path}: {e}")
        return []


def get_servers_from_poller(request: Request) -> List[Server]:
    """Get the current server list from the Poller instance."""
    poller: Poller = request.app.state.poller
    return poller.servers if poller else []


@router.get("/api/servers")
async def get_servers(request: Request):
    """Get list of all configured servers from the Poller."""
    servers = get_servers_from_poller(request)
    logger.debug(f"Returning {len(servers)} servers")
    return [s.dict() for s in servers]


@router.get("/api/servers/{server_id}/status")
async def get_server_status(request: Request, server_id: str):
    """Get the status of a specific server."""
    servers = get_servers_from_poller(request)
    logger.debug(f"Loaded {len(servers)} servers for status request")
    server = next((s for s in servers if s.id == server_id), None)
    if not server:
        logger.warning(f"Server not found: {server_id}")
        raise HTTPException(status_code=404, detail="server not found")

    # 获取全局的 Poller 实例，用于查询服务器状态
    poller: Poller = request.app.state.poller
    logger.debug(f"Fetching status for server: {server_id}")
    
    # 使用服务器 ID 获取状态
    status = poller.get_status(server.id) if poller else None
    
    # 如果未能获取到状态，返回 404 错误
    if not status:
        logger.warning(f"Status not found for server: {server_id}")
        raise HTTPException(status_code=404, detail="status not found")

    # 返回服务器状态的 JSON 响应
    return JSONResponse(content=status.dict())


@router.post("/api/servers/{server_id}/channels/{channel_id}/restart")
async def post_restart_channel(
    request: Request,
    server_id: str,
    channel_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Restart a specific channel on a server.
    
    Requires authentication if API_KEY_ENABLED is True.
    """
    # Validate channel_id format to prevent injection
    # Must start with alphanumeric to avoid command-line option confusion
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$', channel_id):
        logger.warning(f"Invalid channel_id format: {channel_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid channel_id format. Must start with alphanumeric character and contain only alphanumeric characters, hyphens, and underscores."
        )
    
    servers = get_servers_from_poller(request)
    server = next((s for s in servers if s.id == server_id), None)
    if not server:
        logger.warning(f"Server not found for restart: {server_id}")
        raise HTTPException(status_code=404, detail="server not found")
    
    logger.info(f"Restart request for channel {channel_id} on server {server_id}")
    result = await restart_channel(server, channel_id)
    return JSONResponse(content=result)


@router.post("/api/servers/reload")
async def post_reload_servers(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Reload the server configuration from the configuration file.
    
    This allows updating the monitored servers without restarting the application.
    Requires authentication if API_KEY_ENABLED is True.
    """
    logger.info("Reloading server configuration")
    try:
        servers = load_servers()
        if not servers:
            logger.warning("No servers loaded from configuration file")
            raise HTTPException(
                status_code=500,
                detail="Failed to load servers from configuration file"
            )
        
        poller: Poller = request.app.state.poller
        if not poller:
            logger.error("Poller not available")
            raise HTTPException(status_code=500, detail="Poller not available")
        
        await poller.reload_servers(servers)
        logger.info(f"Successfully reloaded {len(servers)} servers")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Reloaded {len(servers)} servers",
            "servers": [s.dict() for s in servers]
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reload servers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload servers: {str(e)}"
        )

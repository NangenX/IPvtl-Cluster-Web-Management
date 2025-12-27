"""通道管理服务"""
import asyncio
import logging
from typing import Optional
import httpx
from app.config import settings
from app.models import ChannelActionResult
from app.services.poller import poller_service

logger = logging.getLogger(__name__)

class ManagerService:
    """通道管理服务"""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    async def start(self):
        """启动管理服务"""
        self._client = httpx.AsyncClient()
        logger.info("Manager service started")
    
    async def stop(self):
        """停止管理服务"""
        if self._client:
            await self._client.aclose()
        logger.info("Manager service stopped")
    
    async def start_channel(self, server_id: str, channel_id: int) -> ChannelActionResult:
        """
        启动指定通道
        API: GET /channel{id}?start
        """
        return await self._channel_action(server_id, channel_id, "start")
    
    async def stop_channel(self, server_id: str, channel_id: int) -> ChannelActionResult:
        """
        停止指定通道
        API: GET /channel{id}?stop
        """
        return await self._channel_action(server_id, channel_id, "stop")
    
    async def restart_channel(self, server_id: str, channel_id: int) -> ChannelActionResult:
        """重启指定通道（先停后启）"""
        server_info = poller_service.get_server(server_id)
        if not server_info:
            return ChannelActionResult(
                success=False,
                message=f"Server not found: {server_id}",
                channel_id=channel_id,
                server_id=server_id
            )
        
        config, _ = server_info
        
        try:
            # 1. 停止通道
            logger.info(f"Stopping channel {channel_id} on {config.name}")
            stop_url = f"{config.base_url}/channel{channel_id}?stop"
            stop_resp = await self._client.get(stop_url, timeout=settings.channel_stop_timeout)
            stop_resp.raise_for_status()
            
            # 2. 等待通道完全停止
            await asyncio.sleep(settings.channel_restart_delay)
            
            # 3. 启动通道
            logger.info(f"Starting channel {channel_id} on {config.name}")
            start_url = f"{config.base_url}/channel{channel_id}?start"
            start_resp = await self._client.get(start_url, timeout=settings.channel_start_timeout)
            start_resp.raise_for_status()
            
            # 4. 刷新状态
            await poller_service.poll_server(server_id)
            
            return ChannelActionResult(
                success=True,
                message="Channel restarted successfully",
                channel_id=channel_id,
                server_id=server_id
            )
            
        except httpx.HTTPStatusError as e:
            msg = f"HTTP error: {e.response.status_code}"
            logger.error(f"Restart channel {channel_id} failed: {msg}")
            return ChannelActionResult(
                success=False, message=msg,
                channel_id=channel_id, server_id=server_id
            )
        except Exception as e:
            msg = str(e)
            logger.error(f"Restart channel {channel_id} failed: {msg}")
            return ChannelActionResult(
                success=False, message=msg,
                channel_id=channel_id, server_id=server_id
            )
    
    async def _channel_action(
        self, server_id: str, channel_id: int, action: str
    ) -> ChannelActionResult:
        """
        执行通道操作
        action: "start" | "stop"
        API: GET /channel{id}?{action}
        """
        server_info = poller_service.get_server(server_id)
        if not server_info:
            return ChannelActionResult(
                success=False,
                message=f"Server not found: {server_id}",
                channel_id=channel_id,
                server_id=server_id
            )
        
        config, _ = server_info
        timeout = (
            settings.channel_start_timeout 
            if action == "start" 
            else settings.channel_stop_timeout
        )
        
        try:
            # 构建 URL: /channel{id}?start 或 /channel{id}?stop
            url = f"{config.base_url}/channel{channel_id}?{action}"
            logger.info(f"Executing {action} on channel {channel_id}: {url}")
            
            resp = await self._client.get(url, timeout=timeout)
            resp.raise_for_status()
            
            # 刷新服务器状态
            await poller_service.poll_server(server_id)
            
            return ChannelActionResult(
                success=True,
                message=f"Channel {action} successful",
                channel_id=channel_id,
                server_id=server_id
            )
            
        except httpx.HTTPStatusError as e:
            msg = f"HTTP error: {e.response.status_code}"
            logger.error(f"Channel {action} failed: {msg}")
            return ChannelActionResult(
                success=False, message=msg,
                channel_id=channel_id, server_id=server_id
            )
        except httpx.ConnectError:
            msg = "Connection refused"
            logger.error(f"Channel {action} failed: {msg}")
            return ChannelActionResult(
                success=False, message=msg,
                channel_id=channel_id, server_id=server_id
            )
        except Exception as e:
            msg = str(e)
            logger.error(f"Channel {action} failed: {msg}")
            return ChannelActionResult(
                success=False, message=msg,
                channel_id=channel_id, server_id=server_id
            )

# 全局单例
manager_service = ManagerService()

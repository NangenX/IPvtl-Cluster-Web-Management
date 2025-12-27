"""状态轮询服务"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import httpx
from app.config import settings
from app.models import (
    ServerConfig, ServerState, ServerStatus,
    ChannelInfo, ChannelState
)

logger = logging.getLogger(__name__)

class PollerService:
    """服务器状态轮询服务"""
    
    def __init__(self):
        self._servers: dict[str, ServerConfig] = {}
        self._states: dict[str, ServerState] = {}
        self._client: Optional[httpx.AsyncClient] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(settings.poll_max_concurrent)
    
    async def start(self):
        """启动轮询服务"""
        self._load_servers()
        self._client = httpx.AsyncClient(timeout=settings.poll_timeout)
        # 立即执行一次轮询
        await self._poll_all()
        # 启动定时轮询
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(f"Poller started, monitoring {len(self._servers)} servers")
    
    async def stop(self):
        """停止轮询服务"""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()
        logger.info("Poller stopped")
    
    def _load_servers(self):
        """从配置文件加载服务器列表"""
        config_path = Path(settings.servers_config_path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("servers", []):
            server = ServerConfig(**item)
            self._servers[server.id] = server
            self._states[server.id] = ServerState(server_id=server.id)
        logger.info(f"Loaded {len(self._servers)} servers from config")
    
    def reload_servers(self):
        """重新加载服务器配置"""
        old_ids = set(self._servers.keys())
        self._servers.clear()
        self._load_servers()
        # 清理已删除服务器的状态
        for sid in old_ids - set(self._servers.keys()):
            self._states.pop(sid, None)
    
    def get_all_servers(self) -> list[tuple[ServerConfig, ServerState]]:
        """获取所有服务器及其状态"""
        return [
            (self._servers[sid], self._states[sid])
            for sid in self._servers
        ]
    
    def get_server(self, server_id: str) -> Optional[tuple[ServerConfig, ServerState]]:
        """获取单个服务器信息"""
        if server_id not in self._servers:
            return None
        return (self._servers[server_id], self._states[server_id])
    
    async def poll_server(self, server_id: str) -> ServerState:
        """手动刷新单个服务器状态"""
        if server_id not in self._servers:
            raise ValueError(f"Server not found: {server_id}")
        await self._poll_single(self._servers[server_id])
        return self._states[server_id]
    
    async def _poll_loop(self):
        """轮询主循环"""
        while True:
            await asyncio.sleep(settings.poll_interval)
            try:
                await self._poll_all()
            except Exception as e:
                logger.error(f"Poll cycle error: {e}")
    
    async def _poll_all(self):
        """并发轮询所有服务器"""
        tasks = [
            self._poll_single(server)
            for server in self._servers.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _poll_single(self, server: ServerConfig):
        """轮询单个服务器 - 调用 /status 接口"""
        async with self._semaphore:
            state = self._states[server.id]
            try:
                # 调用 IPVTL /status 接口
                resp = await self._client.get(f"{server.base_url}/status")
                resp.raise_for_status()
                data = resp.json()
                
                # 解析 CPU 数据
                cpu_cores = data.get("cpu", [])
                cpu_avg = sum(cpu_cores) / len(cpu_cores) if cpu_cores else None
                
                # 解析通道数据
                channels = []
                for idx, ch in enumerate(data.get("channels", [])):
                    channel_id = idx + 1  # 1-based ID
                    try:
                        ch_state = ChannelState(ch.get("state", "idle"))
                    except ValueError:
                        ch_state = ChannelState.IDLE
                    channels.append(ChannelInfo(
                        id=channel_id,
                        state=ch_state,
                        status=ch.get("status", "")
                    ))
                
                # 更新状态
                state.status = ServerStatus.ONLINE
                state.cpu_cores = cpu_cores
                state.cpu_avg = cpu_avg
                state.channels = channels
                state.error_message = None
                state.last_poll_time = datetime.now()
                
                logger.debug(f"Polled {server.name}: {len(channels)} channels, CPU avg {cpu_avg:.1f}%")
                
            except httpx.HTTPStatusError as e:
                state.status = ServerStatus.ERROR
                state.error_message = f"HTTP {e.response.status_code}"
                state.last_poll_time = datetime.now()
                logger.warning(f"Poll {server.name} HTTP error: {e}")
            except httpx.ConnectError:
                state.status = ServerStatus.OFFLINE
                state.error_message = "Connection refused"
                state.last_poll_time = datetime.now()
                logger.warning(f"Poll {server.name}: connection refused")
            except Exception as e:
                state.status = ServerStatus.OFFLINE
                state.error_message = str(e)
                state.last_poll_time = datetime.now()
                logger.warning(f"Poll {server.name} failed: {e}")

# 全局单例
poller_service = PollerService()

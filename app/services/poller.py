import asyncio
import json
from typing import Dict, List

import httpx

from app.config import settings
from app.logging_config import get_logger
from app.models import Server, ServerStatus, Channel

logger = get_logger(__name__)


class Poller:
    def __init__(self, servers: List[Server]):
        self.servers = servers[: settings.MAX_SERVERS]
        self._task: asyncio.Task = None
        self._stop_event = asyncio.Event()
        self._statuses: Dict[str, ServerStatus] = {}
        self._client = httpx.AsyncClient(timeout=settings.HTTPX_TIMEOUT_SECONDS)
        self._semaphore = asyncio.Semaphore(settings.POLL_CONCURRENCY)
        self._lock = asyncio.Lock()  # Thread safety for server list updates

    async def start(self):
        if self._task:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        if not self._task:
            return
        self._stop_event.set()
        await self._task
        self._task = None
        await self._client.aclose()

    async def _fetch(self, server: Server):
        url = f"http://{server.host}:{server.port}/status"
        async with self._semaphore:
            try:
                logger.debug(f"Fetching status from {url} (server id={server.id})")
                r = await self._client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    logger.debug(f"Response from {url}: {data}")
                    # 处理 CPU 数据，计算平均值
                    cpu = sum(data.get("cpu", [])) / len(data.get("cpu", [])) if data.get("cpu") else 0
                    channels = []
                    for c in data.get("channels", []):
                        channels.append(Channel(id=str(c.get("id")), name=c.get("name"), status=c.get("status")))
                    self._statuses[server.id] = ServerStatus(id=server.id, cpu=cpu, channels=channels)
                    logger.debug(f"Updated status for server {server.id}")
                else:
                    logger.error(f"Failed to fetch status from {url} (server id={server.id}), status code: {r.status_code}")
                    # 填充一个默认状态，避免外部请求因不存在状态而返回 404
                    self._statuses[server.id] = ServerStatus(id=server.id, cpu=0.0, channels=[])
            except httpx.TimeoutException as e:
                logger.error(f"Timeout fetching status from {url} (server id={server.id}): {e}")
                self._statuses[server.id] = ServerStatus(id=server.id, cpu=0.0, channels=[])
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching status from {url} (server id={server.id}): {e}")
                self._statuses[server.id] = ServerStatus(id=server.id, cpu=0.0, channels=[])
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error from {url} (server id={server.id}): {e}")
                self._statuses[server.id] = ServerStatus(id=server.id, cpu=0.0, channels=[])
            except Exception as e:
                logger.error(f"Unexpected error fetching status from {url} (server id={server.id}): {e}")
                # 在请求失败时也填充默认状态以避免 API 404
                try:
                    self._statuses[server.id] = ServerStatus(id=server.id, cpu=0.0, channels=[])
                except Exception:
                    # 忽略在错误路径中可能发生的二次异常
                    pass

    async def _run_loop(self):
        while not self._stop_event.is_set():
            logger.info("Running poller loop")
            async with self._lock:
                tasks = [self._fetch(s) for s in self.servers]
            await asyncio.gather(*tasks)
            try:
                await asyncio.wait_for(asyncio.sleep(settings.POLL_INTERVAL), timeout=settings.POLL_INTERVAL + 1)
            except asyncio.TimeoutError:
                pass

    def get_status(self, server_id: str):
        logger.debug(f"Getting status for server {server_id}")
        return self._statuses.get(server_id)

    def get_all(self) -> List[ServerStatus]:
        return list(self._statuses.values())
    
    async def reload_servers(self, servers: List[Server]):
        """
        Reload the server list at runtime.
        
        Args:
            servers: New list of servers to monitor
        """
        async with self._lock:
            logger.info(f"Reloading servers: {len(servers)} servers")
            self.servers = servers[: settings.MAX_SERVERS]
            # Clear statuses for servers that are no longer in the list
            current_server_ids = {s.id for s in self.servers}
            removed_servers = set(self._statuses.keys()) - current_server_ids
            for server_id in removed_servers:
                logger.info(f"Removing status for removed server: {server_id}")
                del self._statuses[server_id]
            logger.info("Server list reloaded successfully")

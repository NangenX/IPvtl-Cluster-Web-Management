import asyncio
import json
from typing import Dict, List

import httpx

from app.config import settings
from app.models import Server, ServerStatus, Channel


class Poller:
    def __init__(self, servers: List[Server]):
        self.servers = servers[: settings.MAX_SERVERS]
        self._task: asyncio.Task = None
        self._stop_event = asyncio.Event()
        self._statuses: Dict[str, ServerStatus] = {}
        self._client = httpx.AsyncClient(timeout=settings.HTTPX_TIMEOUT_SECONDS)
        self._semaphore = asyncio.Semaphore(settings.POLL_CONCURRENCY)

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
                print(f"Fetching status from {url} (server id={server.id})")  # 调试日志
                r = await self._client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    print(f"Response from {url}: {data}")  # 调试日志
                    # 处理 CPU 数据，计算平均值
                    cpu = sum(data.get("cpu", [])) / len(data.get("cpu", [])) if data.get("cpu") else 0
                    channels = []
                    for c in data.get("channels", []):
                        channels.append(Channel(id=str(c.get("id")), name=c.get("name"), status=c.get("status")))
                    self._statuses[server.id] = ServerStatus(id=server.id, cpu=cpu, channels=channels)
                    print(f"Updated statuses: {self._statuses}")  # 调试日志
                else:
                    print(f"Failed to fetch status from {url} (server id={server.id}), status code: {r.status_code}")
                    # 填充一个默认状态，避免外部请求因不存在状态而返回 404
                    self._statuses[server.id] = ServerStatus(id=server.id, cpu=0.0, channels=[])
            except Exception as e:
                print(f"Error fetching status from {url} (server id={server.id}): {e}")  # 调试日志
                # 在请求失败时也填充默认状态以避免 API 404
                try:
                    self._statuses[server.id] = ServerStatus(id=server.id, cpu=0.0, channels=[])
                except Exception:
                    # 忽略在错误路径中可能发生的二次异常
                    pass

    async def _run_loop(self):
        while not self._stop_event.is_set():
            print("Running poller loop")  # 调试日志
            tasks = [self._fetch(s) for s in self.servers]
            await asyncio.gather(*tasks)
            try:
                await asyncio.wait_for(asyncio.sleep(settings.POLL_INTERVAL), timeout=settings.POLL_INTERVAL + 1)
            except asyncio.TimeoutError:
                pass

    def get_status(self, server_id: str):
        print(f"Current statuses: {self._statuses}")  # 添加调试日志
        return self._statuses.get(server_id)

    def get_all(self) -> List[ServerStatus]:
        return list(self._statuses.values())

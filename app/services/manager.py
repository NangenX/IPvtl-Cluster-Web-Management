import asyncio
import httpx
from typing import Tuple

from app.config import settings
from app.models import Server


async def stop_channel(server: Server, channel_id: str) -> Tuple[bool, str]:
    url = f"http://{server.host}:{server.port or 80}/channel{channel_id}?stop"
    try:
        async with httpx.AsyncClient(timeout=settings.RESTART_STOP_TIMEOUT_SECONDS) as c:
            r = await c.get(url)
            return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)


async def start_channel(server: Server, channel_id: str) -> Tuple[bool, str]:
    url = f"http://{server.host}:{server.port or 80}/channel{channel_id}?start"
    try:
        async with httpx.AsyncClient(timeout=settings.RESTART_START_TIMEOUT_SECONDS) as c:
            r = await c.get(url)
            return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)


async def restart_channel(server: Server, channel_id: str) -> dict:
    # conservative: stop then start
    stop_ok, stop_msg = await stop_channel(server, channel_id)
    await asyncio.sleep(0.5)
    start_ok, start_msg = await start_channel(server, channel_id)
    return {
        "server_id": server.id,
        "channel_id": channel_id,
        "stop": {"ok": stop_ok, "msg": stop_msg},
        "start": {"ok": start_ok, "msg": start_msg},
    }

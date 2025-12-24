import asyncio
import httpx
from typing import Tuple

from app.config import settings
from app.logging_config import get_logger
from app.models import Server

logger = get_logger(__name__)


async def stop_channel(server: Server, channel_id: str) -> Tuple[bool, str]:
    url = f"http://{server.host}:{server.port or 80}/channel{channel_id}?stop"
    try:
        logger.info(f"Stopping channel {channel_id} on server {server.id}")
        async with httpx.AsyncClient(timeout=settings.RESTART_STOP_TIMEOUT_SECONDS) as c:
            r = await c.get(url)
            success = r.status_code == 200
            if success:
                logger.info(f"Successfully stopped channel {channel_id} on server {server.id}")
            else:
                logger.error(f"Failed to stop channel {channel_id} on server {server.id}: HTTP {r.status_code}")
            return success, r.text
    except httpx.TimeoutException as e:
        logger.error(f"Timeout stopping channel {channel_id} on server {server.id}: {e}")
        return False, f"Timeout: {str(e)}"
    except httpx.HTTPError as e:
        logger.error(f"HTTP error stopping channel {channel_id} on server {server.id}: {e}")
        return False, f"HTTP Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error stopping channel {channel_id} on server {server.id}: {e}")
        return False, str(e)


async def start_channel(server: Server, channel_id: str) -> Tuple[bool, str]:
    url = f"http://{server.host}:{server.port or 80}/channel{channel_id}?start"
    try:
        logger.info(f"Starting channel {channel_id} on server {server.id}")
        async with httpx.AsyncClient(timeout=settings.RESTART_START_TIMEOUT_SECONDS) as c:
            r = await c.get(url)
            success = r.status_code == 200
            if success:
                logger.info(f"Successfully started channel {channel_id} on server {server.id}")
            else:
                logger.error(f"Failed to start channel {channel_id} on server {server.id}: HTTP {r.status_code}")
            return success, r.text
    except httpx.TimeoutException as e:
        logger.error(f"Timeout starting channel {channel_id} on server {server.id}: {e}")
        return False, f"Timeout: {str(e)}"
    except httpx.HTTPError as e:
        logger.error(f"HTTP error starting channel {channel_id} on server {server.id}: {e}")
        return False, f"HTTP Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error starting channel {channel_id} on server {server.id}: {e}")
        return False, str(e)


async def restart_channel(server: Server, channel_id: str) -> dict:
    # conservative: stop then start
    logger.info(f"Restarting channel {channel_id} on server {server.id}")
    stop_ok, stop_msg = await stop_channel(server, channel_id)
    await asyncio.sleep(settings.RESTART_DELAY_SECONDS)
    start_ok, start_msg = await start_channel(server, channel_id)
    
    result = {
        "server_id": server.id,
        "channel_id": channel_id,
        "stop": {"ok": stop_ok, "msg": stop_msg},
        "start": {"ok": start_ok, "msg": start_msg},
    }
    
    if stop_ok and start_ok:
        logger.info(f"Successfully restarted channel {channel_id} on server {server.id}")
    else:
        logger.warning(f"Restart channel {channel_id} on server {server.id} completed with issues: stop={stop_ok}, start={start_ok}")
    
    return result

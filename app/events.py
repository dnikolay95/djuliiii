import logging
from typing import Any, Dict

import aiohttp

logger = logging.getLogger(__name__)


async def send_event(backend_url: str, auth_secret: str, event: Dict[str, Any]) -> None:
    """Send event to backend for websocket broadcast."""
    url = f"{backend_url.rstrip('/')}/api/internal/events"
    headers = {"X-Auth-Secret": auth_secret, "Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=event, headers=headers, timeout=5) as resp:
                if resp.status >= 300:
                    text = await resp.text()
                    logger.warning("Failed to send event: %s %s", resp.status, text)
    except Exception:
        logger.exception("Failed to send event to backend")


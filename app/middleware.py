import json
import logging
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from .db import Database, utc_now
from .events import send_event

logger = logging.getLogger(__name__)


def extract_message_payload(message: Message) -> Dict[str, Any]:
    return {
        "message_id": message.message_id,
        "content_type": message.content_type,
        "date": message.date.isoformat() if message.date else None,
    }


def get_message_text(message: Message) -> str | None:
    return message.text or message.caption


def get_message_type(message: Message) -> str:
    return message.content_type or "unknown"


class MessageLoggingMiddleware(BaseMiddleware):
    def __init__(self, db: Database, backend_url: str | None = None, backend_secret: str | None = None) -> None:
        super().__init__()
        self.db = db
        self.backend_url = backend_url
        self.backend_secret = backend_secret

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user:
            try:
                await self.db.upsert_user(
                    tg_user_id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                    seen_at=utc_now(),
                )
                await self.db.add_message(
                    tg_user_id=user.id,
                    message_text=get_message_text(event),
                    message_type=get_message_type(event),
                    raw_payload=json.dumps(extract_message_payload(event)),
                    received_at=utc_now(),
                )
                if self.backend_url and self.backend_secret:
                    await send_event(
                        self.backend_url,
                        self.backend_secret,
                        {
                            "type": "message_received",
                            "user_id": user.id,
                            "message_type": get_message_type(event),
                            "message_text": get_message_text(event),
                        },
                    )
            except Exception:
                logger.exception("Failed to log incoming message for user_id=%s", user.id)
        return await handler(event, data)


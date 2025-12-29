import logging

import logging
from typing import Optional

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, User

from .db import Database
from .events import send_event
from .keyboards import get_start_kb
from .texts import get_random_greeting

logger = logging.getLogger(__name__)

router = Router()
db: Optional[Database] = None
backend_url: Optional[str] = None
backend_secret: Optional[str] = None


def set_db(database: Database) -> None:
    global db
    db = database


def set_event_sender(url: str, secret: str) -> None:
    global backend_url, backend_secret
    backend_url = url
    backend_secret = secret


async def upsert_from_user(user: User) -> None:
    if not db:
        logger.warning("Database is not initialized; cannot upsert user.")
        return
    await db.upsert_user(
        tg_user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        seen_at=None,
    )
    if backend_url and backend_secret:
        await send_event(
            backend_url,
            backend_secret,
            {
                "type": "user_upserted",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
        )


async def log_greeting(user: User, greeting: str) -> None:
    if not db:
        logger.warning("Database is not initialized; cannot log greeting.")
        return
    await db.add_greeting(tg_user_id=user.id, greeting_text=greeting)
    if backend_url and backend_secret:
        await send_event(
            backend_url,
            backend_secret,
            {"type": "greeting_sent", "user_id": user.id, "text": greeting},
        )


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    name = (message.from_user.first_name or "").strip() or "друг"
    text = (
        f"Привет, {name}! Нажми кнопку ниже, чтобы получить "
        "поздравление с Новым годом."
    )
    logger.info("Sending greeting prompt to user_id=%s", message.from_user.id)
    await message.answer(text, reply_markup=get_start_kb())


@router.callback_query(lambda c: c.data == "get_greeting")
async def handle_greeting(callback: CallbackQuery) -> None:
    if callback.from_user:
        await upsert_from_user(callback.from_user)
    greeting = get_random_greeting()
    logger.info("Sending random greeting to user_id=%s", callback.from_user.id)
    if callback.from_user:
        await log_greeting(callback.from_user, greeting)
    if callback.message:
        await callback.message.answer(greeting)
    await callback.answer()


@router.message(Command("info"))
async def handle_info(message: Message) -> None:
    logger.info("Sending info to user_id=%s", message.from_user.id)
    await message.answer(
        "Это бот, который создан для поднятия новогоднего настроения."
    )


@router.message(Command("greet"))
async def handle_greet(message: Message) -> None:
    greeting = get_random_greeting()
    logger.info("Sending random greeting to user_id=%s", message.from_user.id)
    await log_greeting(message.from_user, greeting)
    await message.answer(greeting)


@router.message()
async def handle_any_message(message: Message) -> None:
    # Заглушка, чтобы middleware отработало и залогировало любые сообщения без ответа.
    if message.from_user:
        await upsert_from_user(message.from_user)



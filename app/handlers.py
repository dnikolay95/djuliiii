import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from .keyboards import get_start_kb
from .texts import get_random_greeting

logger = logging.getLogger(__name__)

router = Router()


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
    greeting = get_random_greeting()
    logger.info("Sending random greeting to user_id=%s", callback.from_user.id)
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
    await message.answer(greeting)



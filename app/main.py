import asyncio
import logging

from aiogram import Bot, Dispatcher

from .commands import set_bot_commands
from .config import load_settings
from .db import Database
from .handlers import router, set_db, set_event_sender
from .middleware import MessageLoggingMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    db = await Database.create(settings.db_path)
    set_db(db)
    set_event_sender(settings.backend_url, settings.auth_secret)
    dp.message.middleware(
        MessageLoggingMiddleware(db, backend_url=settings.backend_url, backend_secret=settings.auth_secret)
    )

    logging.info("Setting bot commands...")
    await set_bot_commands(bot)
    logging.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



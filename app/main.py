import asyncio
import logging

from aiogram import Bot, Dispatcher

from .config import load_settings
from .handlers import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    logging.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



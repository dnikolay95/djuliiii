from aiogram import Bot
from aiogram.types import BotCommand


async def set_bot_commands(bot: Bot) -> None:
    """Configure bot commands for Telegram menu."""
    commands = [
        BotCommand(command="info", description="О боте"),
        BotCommand(command="greet", description="Случайное поздравление"),
    ]
    await bot.set_my_commands(commands)

import logging
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeDefault

logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    """Register bot commands for Telegram menu."""
    commands = [
        BotCommand(command="info", description="О боте"),
        BotCommand(command="greet", description="Случайное поздравление"),
    ]
    scopes = [
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
    ]
    for scope in scopes:
        await bot.set_my_commands(commands, scope=scope)
    logger.info(
        "Bot commands are set for scopes: %s",
        ", ".join(scope.type for scope in scopes),
    )



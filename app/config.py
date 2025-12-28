import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    bot_token: str


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "Environment variable BOT_TOKEN is missing or empty. "
            "Please set it in the .env file."
        )
    logger.debug("BOT_TOKEN loaded successfully.")
    return Settings(bot_token=token)



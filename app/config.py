import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    bot_token: str
    db_path: str
    auth_secret: str
    admin_login: str
    admin_password: str
    backend_url: str


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "Environment variable BOT_TOKEN is missing or empty. "
            "Please set it in the .env file."
        )
    db_path = os.getenv("DB_PATH", "./data/bot.db").strip() or "./data/bot.db"
    auth_secret = os.getenv("AUTH_SECRET", "change_me_secret").strip() or "change_me_secret"
    admin_login = os.getenv("ADMIN_LOGIN", "admin").strip() or "admin"
    admin_password = os.getenv("ADMIN_PASSWORD", "admin2").strip() or "admin2"
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8011").strip() or "http://localhost:8011"
    logger.debug("Settings loaded successfully.")
    return Settings(
        bot_token=token,
        db_path=db_path,
        auth_secret=auth_secret,
        admin_login=admin_login,
        admin_password=admin_password,
        backend_url=backend_url,
    )



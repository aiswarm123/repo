from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    support_chat_id: int
    database_path: str


def load_config() -> Config:
    token = getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is required")

    support_chat_id = getenv("SUPPORT_CHAT_ID")
    if not support_chat_id:
        raise ValueError("SUPPORT_CHAT_ID environment variable is required")

    return Config(
        bot_token=token,
        support_chat_id=int(support_chat_id),
        database_path=getenv("DATABASE_PATH", "support.db"),
    )

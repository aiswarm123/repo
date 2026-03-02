from dataclasses import dataclass, field
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    support_chat_id: int
    database_path: str
    admin_ids: list[int] = field(default_factory=list)


def load_config() -> Config:
    token = getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is required")

    support_chat_id = getenv("SUPPORT_CHAT_ID")
    if not support_chat_id:
        raise ValueError("SUPPORT_CHAT_ID environment variable is required")

    admin_ids = [int(x) for x in getenv("ADMIN_IDS", "").split(",") if x]

    return Config(
        bot_token=token,
        support_chat_id=int(support_chat_id),
        database_path=getenv("DATABASE_PATH", "support.db"),
        admin_ids=admin_ids,
    )

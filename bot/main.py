"""Entry point for the Telegram support bot."""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import load_config
from bot.db.queries import init_db
from bot.handlers import admin, support, user
from bot.middlewares.ban_check import BanCheckMiddleware
from bot.middlewares.i18n import I18nMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()

    await init_db(config.database_path)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Inject dependencies into handlers via middleware data
    dp["db_path"] = config.database_path
    dp["support_chat_id"] = config.support_chat_id

    dp.update.middleware(I18nMiddleware())

    # Restrict admin router to configured admin user IDs
    admin_ids = set(config.admin_ids)
    admin.router.message.filter(F.from_user.id.in_(admin_ids))
    admin.router.callback_query.filter(F.from_user.id.in_(admin_ids))

    # BanCheckMiddleware runs before all user and support handlers.
    # It is NOT applied to the admin router so admins are never blocked.
    ban_middleware = BanCheckMiddleware()
    user.router.message.middleware(ban_middleware)
    user.router.callback_query.middleware(ban_middleware)
    support.router.message.middleware(ban_middleware)

    # Admin router is included first so its filters take priority
    dp.include_router(admin.router)
    dp.include_router(user.router)
    dp.include_router(support.router)

    logger.info("Starting bot...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())

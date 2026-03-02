"""Internationalization middleware for the support bot."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.db import queries
from bot.locales import make_t


class I18nMiddleware(BaseMiddleware):
    """Inject ``lang`` and ``t`` into handler data based on user's stored language."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        lang = "en"
        db_path: str | None = data.get("db_path")

        if db_path:
            # Resolve user_id from the update
            user = None
            update: Update | None = data.get("event_update")
            if update is None:
                # Fallback: try to get from event itself
                update = event if isinstance(event, Update) else None

            if update is not None:
                if update.message and update.message.from_user:
                    user = update.message.from_user
                elif update.callback_query and update.callback_query.from_user:
                    user = update.callback_query.from_user

            if user is not None:
                lang = await queries.get_user_language(db_path, user.id)

        data["lang"] = lang
        data["t"] = make_t(lang)

        return await handler(event, data)

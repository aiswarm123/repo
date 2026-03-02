"""Middleware that blocks banned users from interacting with user handlers."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.db import queries


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user

        if user:
            db_path: str | None = data.get("db_path")
            if db_path and await queries.is_banned(db_path, user.id):
                if isinstance(event, Message):
                    await event.answer("You are not allowed to use this bot.")
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "You are not allowed to use this bot.", show_alert=True
                    )
                return

        return await handler(event, data)

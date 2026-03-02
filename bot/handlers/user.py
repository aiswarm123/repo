"""Handlers for regular users: /start, /help, /mystatus, /cancel, /language, and relay."""

import logging
from typing import Callable

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db import queries
from bot.keyboards.user import language_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, t: Callable[[str], str], db_path: str) -> None:
    user = message.from_user
    # Auto-detect language on first /start from Telegram language_code
    if user and db_path:
        stored = await queries.get_user_language(db_path, user.id)
        if stored == "en" and user.language_code in ("ru", "uk"):
            await queries.set_user_language(db_path, user.id, user.language_code)
            from bot.locales import make_t
            t = make_t(user.language_code)

    name = user.first_name if user else "there"
    await message.answer(t("start").format(name=name))


@router.message(Command("help"))
async def cmd_help(message: Message, t: Callable[[str], str]) -> None:
    await message.answer(t("help"))


@router.message(Command("language"))
async def cmd_language(message: Message, t: Callable[[str], str]) -> None:
    await message.answer(t("language_choose"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def language_callback(
    callback: CallbackQuery,
    t: Callable[[str], str],
    db_path: str,
) -> None:
    lang = callback.data.split(":")[1]  # type: ignore[union-attr]
    user = callback.from_user
    if user and db_path:
        await queries.set_user_language(db_path, user.id, lang)
    from bot.locales import make_t
    t = make_t(lang)
    await callback.message.edit_text(t("language_set"))  # type: ignore[union-attr]
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(
    message: Message,
    t: Callable[[str], str],
    db_path: str,
    support_chat_id: int,
) -> None:
    """Close the user's current open conversation."""
    user = message.from_user
    if not user:
        return
    ticket = await queries.get_open_ticket_by_user(db_path, user.id)
    if not ticket:
        await message.answer(t("cancel_nothing"))
        return
    await queries.resolve_ticket(db_path, ticket["id"])
    await message.answer(t("cancelled"))
    logger.info("User %d cancelled conversation (ticket #%d)", user.id, ticket["id"])
    try:
        await message.bot.send_message(  # type: ignore[union-attr]
            support_chat_id,
            f"ℹ️ User closed the conversation (ticket #{ticket['id']}).",
        )
    except Exception:
        pass


@router.message(Command("mystatus"))
async def cmd_mystatus(message: Message, t: Callable[[str], str], db_path: str) -> None:
    user = message.from_user
    if not user:
        return
    ticket = await queries.get_open_ticket_by_user(db_path, user.id)
    if not ticket:
        await message.answer(t("mystatus_none"))
        return

    msgs = await queries.get_messages(db_path, ticket["id"])
    history = ""
    if msgs:
        lines = []
        for m in msgs[-10:]:  # last 10 messages
            prefix = "You" if m["direction"] == "user" else "Support"
            lines.append(f"<b>{prefix}:</b> {m['text']}")
        history = "\n\n<b>Recent messages:</b>\n" + "\n".join(lines)

    await message.answer(
        f"<b>Conversation #{ticket['id']}</b>\n"
        f"Status: {ticket['status']}\n"
        f"Started: {ticket['created_at']}"
        f"{history}",
        parse_mode="HTML",
    )


# ── Catch-all relay ───────────────────────────────────────────────────────────


@router.message(F.text, ~F.text.startswith("/"))
async def relay_user_message(
    message: Message,
    bot: Bot,
    db_path: str,
    support_chat_id: int,
    t: Callable[[str], str],
) -> None:
    """Forward any non-command text to the support chat thread."""
    user = message.from_user
    if not user or not message.text:
        return

    ticket = await queries.get_open_ticket_by_user(db_path, user.id)

    if ticket:
        # Existing open conversation — append to thread
        await queries.append_message(db_path, ticket["id"], "user", user.id, message.text)
        try:
            await bot.send_message(
                support_chat_id,
                f"<b>{user.first_name}:</b> {message.text}",
                reply_to_message_id=ticket["thread_msg_id"],
                parse_mode="HTML",
            )
        except Exception:
            logger.warning("Could not relay message to support chat for ticket #%d", ticket["id"])
        await message.answer(t("relay_sent"))
    else:
        # New conversation — create ticket, forward opening message
        ticket_id = await queries.create_ticket(db_path, user.id, user.username)
        await queries.append_message(db_path, ticket_id, "user", user.id, message.text)

        username_display = f"@{user.username}" if user.username else f"ID:{user.id}"
        try:
            fwd = await bot.send_message(
                support_chat_id,
                f"💬 <b>New conversation</b> — {user.full_name} ({username_display}, "
                f"<code>{user.id}</code>)\n\n{message.text}\n\n"
                f"<i>Reply to this thread to respond. Use /resolve {ticket_id} to close.</i>",
                parse_mode="HTML",
            )
            await queries.set_thread_msg_id(db_path, ticket_id, fwd.message_id)
        except Exception:
            logger.warning("Could not forward new ticket #%d to support chat", ticket_id)

        await message.answer(t("relay_new"))
        logger.info("Ticket #%d created by user %d", ticket_id, user.id)

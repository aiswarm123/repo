"""Handlers for regular users: /start, /help, /ticket FSM flow, /language."""

import logging
from typing import Callable

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db import queries
from bot.keyboards.user import cancel_keyboard, language_keyboard, ticket_submitted_keyboard
from bot.states.ticket import TicketForm

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


@router.message(Command("ticket"))
async def cmd_ticket(message: Message, state: FSMContext, t: Callable[[str], str]) -> None:
    await state.set_state(TicketForm.waiting_for_subject)
    await message.answer(t("ticket_ask_subject"), reply_markup=cancel_keyboard())


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext, t: Callable[[str], str]) -> None:
    await state.clear()
    await callback.message.edit_text(t("cancelled"))  # type: ignore[union-attr]
    await callback.answer()


@router.message(TicketForm.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext, t: Callable[[str], str]) -> None:
    if not message.text:
        await message.answer(t("ticket_subject_invalid"))
        return
    await state.update_data(subject=message.text)
    await state.set_state(TicketForm.waiting_for_body)
    await message.answer(t("ticket_ask_body"), reply_markup=cancel_keyboard())


@router.message(TicketForm.waiting_for_body)
async def process_body(
    message: Message,
    state: FSMContext,
    t: Callable[[str], str],
    db_path: str,
    support_chat_id: int,
) -> None:
    if not message.text:
        await message.answer(t("ticket_body_invalid"))
        return

    data = await state.get_data()
    subject: str = data["subject"]
    body: str = message.text
    user = message.from_user

    ticket_id = await queries.create_ticket(
        db_path=db_path,
        user_id=user.id,  # type: ignore[union-attr]
        username=user.username if user else None,  # type: ignore[union-attr]
        subject=subject,
        body=body,
    )

    await state.clear()

    await message.answer(
        t("ticket_submitted").format(id=ticket_id),
        reply_markup=ticket_submitted_keyboard(ticket_id),
    )

    # Notify support chat
    username_display = f"@{user.username}" if user and user.username else str(user.id if user else "unknown")  # type: ignore[union-attr]
    await message.bot.send_message(  # type: ignore[union-attr]
        support_chat_id,
        f"📩 <b>New ticket #{ticket_id}</b>\n"
        f"From: {username_display}\n"
        f"Subject: {subject}\n\n"
        f"{body}\n\n"
        f"Reply with: <code>/reply {ticket_id} &lt;message&gt;</code>\n"
        f"Resolve with: <code>/resolve {ticket_id}</code>",
        parse_mode="HTML",
    )
    logger.info("Ticket #%d created by user %d", ticket_id, user.id if user else 0)  # type: ignore[union-attr]


@router.message(Command("mystatus"))
async def cmd_mystatus(message: Message, t: Callable[[str], str], db_path: str) -> None:
    args = message.text.split() if message.text else []  # type: ignore[union-attr]
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Usage: /mystatus <ticket_id>")
        return

    ticket_id = int(args[1])
    ticket = await queries.get_ticket(db_path, ticket_id)

    if not ticket:
        await message.answer(f"Ticket #{ticket_id} not found.")
        return

    # Only allow the ticket owner to check
    if ticket["user_id"] != message.from_user.id:  # type: ignore[union-attr]
        await message.answer("You don't have permission to view that ticket.")
        return

    replies = await queries.get_replies(db_path, ticket_id)
    reply_text = ""
    if replies:
        reply_text = "\n\n<b>Replies:</b>\n" + "\n".join(
            f"• {r['body']}" for r in replies
        )

    await message.answer(
        f"<b>Ticket #{ticket_id}</b>\n"
        f"Subject: {ticket['subject']}\n"
        f"Status: {ticket['status']}\n"
        f"Created: {ticket['created_at']}"
        f"{reply_text}",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("status:"))
async def status_callback(callback: CallbackQuery, db_path: str) -> None:
    ticket_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    ticket = await queries.get_ticket(db_path, ticket_id)

    if not ticket:
        await callback.answer(f"Ticket #{ticket_id} not found.", show_alert=True)
        return

    await callback.answer(
        f"Ticket #{ticket_id} status: {ticket['status']}", show_alert=True
    )

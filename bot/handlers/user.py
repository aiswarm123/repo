"""Handlers for regular users: /start, /help, /ticket FSM, /mystatus, /cancel, /language, and relay."""

import logging
from typing import Callable

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db import queries
from bot.keyboards.support import ticket_notification_keyboard
from bot.keyboards.user import (
    MENU_HELP,
    MENU_LANGUAGE,
    MENU_MY_TICKETS,
    MENU_OPEN_TICKET,
    cancel_keyboard,
    confirm_ticket_keyboard,
    help_keyboard,
    language_keyboard,
    main_menu_keyboard,
    my_tickets_keyboard,
    open_ticket_inline_keyboard,
    ticket_detail_keyboard,
    ticket_submitted_keyboard,
)
from bot.states.ticket import TicketForm

logger = logging.getLogger(__name__)
router = Router()


# ── /start ────────────────────────────────────────────────────────────────────


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
    # Establish persistent reply keyboard with welcome message
    await message.answer(t("start").format(name=name), reply_markup=main_menu_keyboard())
    # Inline quick-action button
    await message.answer(t("start_choose_action"), reply_markup=open_ticket_inline_keyboard())


# ── /help ─────────────────────────────────────────────────────────────────────


@router.message(Command("help"))
@router.message(StateFilter(None), F.text == MENU_HELP)
async def cmd_help(message: Message, t: Callable[[str], str]) -> None:
    await message.answer(t("help_choose"), reply_markup=help_keyboard())


@router.callback_query(F.data.startswith("help:"))
async def help_category_callback(
    callback: CallbackQuery,
    t: Callable[[str], str],
    state: FSMContext,
) -> None:
    category = (callback.data or "").split(":")[1]
    if category == "tickets":
        await callback.message.edit_text(t("help_tickets_info"), parse_mode="HTML")  # type: ignore[union-attr]
    elif category == "account":
        await callback.message.edit_text(t("help_account_info"), parse_mode="HTML")  # type: ignore[union-attr]
    elif category == "billing":
        await callback.message.edit_text(t("help_billing_info"), parse_mode="HTML")  # type: ignore[union-attr]
    elif category == "contact":
        await state.set_state(TicketForm.waiting_for_subject)
        await callback.message.answer(t("ticket_ask_subject"), reply_markup=cancel_keyboard())  # type: ignore[union-attr]
    await callback.answer()


# ── /language ─────────────────────────────────────────────────────────────────


@router.message(Command("language"))
@router.message(StateFilter(None), F.text == MENU_LANGUAGE)
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
    # Re-establish main menu keyboard after language change
    await callback.message.answer(t("start_choose_action"), reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()


# ── /cancel (relay conversation) ──────────────────────────────────────────────


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


# ── /ticket FSM ───────────────────────────────────────────────────────────────


@router.message(Command("ticket"))
@router.message(StateFilter(None), F.text == MENU_OPEN_TICKET)
async def cmd_ticket(message: Message, state: FSMContext, t: Callable[[str], str]) -> None:
    await state.set_state(TicketForm.waiting_for_subject)
    await message.answer(t("ticket_ask_subject"), reply_markup=cancel_keyboard())


@router.callback_query(F.data == "ticket:open")
async def ticket_open_callback(
    callback: CallbackQuery, state: FSMContext, t: Callable[[str], str]
) -> None:
    await state.set_state(TicketForm.waiting_for_subject)
    await callback.message.answer(t("ticket_ask_subject"), reply_markup=cancel_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_callback(
    callback: CallbackQuery, state: FSMContext, t: Callable[[str], str]
) -> None:
    await state.clear()
    await callback.message.edit_text(t("cancelled"))  # type: ignore[union-attr]
    await callback.answer()


@router.message(TicketForm.waiting_for_subject)
async def process_subject(
    message: Message, state: FSMContext, t: Callable[[str], str]
) -> None:
    if not message.text:
        await message.answer(t("ticket_subject_invalid"))
        return
    await state.update_data(subject=message.text)
    await state.set_state(TicketForm.waiting_for_body)
    await message.answer(t("ticket_ask_body"), reply_markup=cancel_keyboard())


@router.message(TicketForm.waiting_for_body)
async def process_body(
    message: Message, state: FSMContext, t: Callable[[str], str]
) -> None:
    if not message.text:
        await message.answer(t("ticket_body_invalid"))
        return
    await state.update_data(body=message.text)
    await state.set_state(TicketForm.confirming)
    data = await state.get_data()
    await message.answer(
        t("ticket_confirm").format(subject=data["subject"], body=data["body"]),
        reply_markup=confirm_ticket_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "ticket:submit")
async def ticket_submit_callback(
    callback: CallbackQuery,
    state: FSMContext,
    t: Callable[[str], str],
    db_path: str,
    support_chat_id: int,
) -> None:
    data = await state.get_data()
    subject: str = data.get("subject", "")
    body: str = data.get("body", "")
    user = callback.from_user

    ticket_id = await queries.create_ticket(
        db_path=db_path,
        user_id=user.id,  # type: ignore[union-attr]
        username=user.username if user else None,  # type: ignore[union-attr]
        subject=subject,
        body=body,
    )
    await state.clear()

    await callback.message.edit_text(  # type: ignore[union-attr]
        t("ticket_submitted").format(id=ticket_id),
        reply_markup=ticket_submitted_keyboard(ticket_id),
    )
    await callback.answer()

    username_display = (
        f"@{user.username}" if user and user.username  # type: ignore[union-attr]
        else str(user.id if user else "unknown")  # type: ignore[union-attr]
    )
    await callback.bot.send_message(  # type: ignore[union-attr]
        support_chat_id,
        f"🎫 <b>New ticket #{ticket_id}</b>\n"
        f"From: {username_display}\n"
        f"Subject: {subject}\n\n"
        f"{body}",
        parse_mode="HTML",
        reply_markup=ticket_notification_keyboard(ticket_id),
    )
    logger.info("Ticket #%d created by user %d", ticket_id, user.id if user else 0)  # type: ignore[union-attr]


@router.callback_query(F.data == "ticket:edit")
async def ticket_edit_callback(
    callback: CallbackQuery, state: FSMContext, t: Callable[[str], str]
) -> None:
    await state.clear()
    await state.set_state(TicketForm.waiting_for_subject)
    await callback.message.edit_text(t("ticket_ask_subject"), reply_markup=cancel_keyboard())  # type: ignore[union-attr]
    await callback.answer()


# ── /mystatus ─────────────────────────────────────────────────────────────────


@router.message(Command("mystatus"))
@router.message(StateFilter(None), F.text == MENU_MY_TICKETS)
async def cmd_mystatus(message: Message, t: Callable[[str], str], db_path: str) -> None:
    user = message.from_user
    if not user:
        return
    tickets = await queries.get_user_tickets(db_path, user.id)
    if not tickets:
        await message.answer(t("mystatus_none"))
        return
    await message.answer(t("mystatus_header"), reply_markup=my_tickets_keyboard(tickets))


@router.callback_query(F.data == "ticket:list")
async def ticket_list_callback(
    callback: CallbackQuery, t: Callable[[str], str], db_path: str
) -> None:
    user = callback.from_user
    if not user:
        await callback.answer()
        return
    tickets = await queries.get_user_tickets(db_path, user.id)
    if not tickets:
        await callback.message.edit_text(t("mystatus_none"))  # type: ignore[union-attr]
    else:
        await callback.message.edit_text(  # type: ignore[union-attr]
            t("mystatus_header"),
            reply_markup=my_tickets_keyboard(tickets),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket:view:"))
async def ticket_view_callback(
    callback: CallbackQuery, t: Callable[[str], str], db_path: str
) -> None:
    ticket_id = int((callback.data or "").split(":")[2])
    user = callback.from_user
    ticket = await queries.get_ticket(db_path, ticket_id)

    if not ticket or (user and ticket["user_id"] != user.id):
        await callback.answer(t("ticket_not_found"), show_alert=True)
        return

    is_open = ticket["status"] == "open"
    subject = ticket.get("subject") or f"Ticket #{ticket['id']}"
    text = t("ticket_detail").format(
        id=ticket["id"],
        subject=subject,
        status=ticket["status"],
        created_at=ticket["created_at"][:10],
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        reply_markup=ticket_detail_keyboard(ticket_id, is_open),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket:refresh:"))
async def ticket_refresh_callback(
    callback: CallbackQuery, t: Callable[[str], str], db_path: str
) -> None:
    ticket_id = int((callback.data or "").split(":")[2])
    user = callback.from_user
    ticket = await queries.get_ticket(db_path, ticket_id)

    if not ticket or (user and ticket["user_id"] != user.id):
        await callback.answer(t("ticket_not_found"), show_alert=True)
        return

    is_open = ticket["status"] == "open"
    subject = ticket.get("subject") or f"Ticket #{ticket['id']}"
    text = t("ticket_detail").format(
        id=ticket["id"],
        subject=subject,
        status=ticket["status"],
        created_at=ticket["created_at"][:10],
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        reply_markup=ticket_detail_keyboard(ticket_id, is_open),
        parse_mode="HTML",
    )
    await callback.answer("Refreshed!")


@router.callback_query(F.data.startswith("ticket:close:"))
async def ticket_close_callback(
    callback: CallbackQuery, t: Callable[[str], str], db_path: str
) -> None:
    ticket_id = int((callback.data or "").split(":")[2])
    user = callback.from_user
    ticket = await queries.get_ticket(db_path, ticket_id)

    if not ticket or (user and ticket["user_id"] != user.id):
        await callback.answer(t("ticket_not_found"), show_alert=True)
        return

    updated = await queries.resolve_ticket(db_path, ticket_id)
    if updated:
        await callback.message.edit_text(t("ticket_closed").format(id=ticket_id))  # type: ignore[union-attr]
        await callback.answer()
    else:
        await callback.answer("Ticket is already closed.", show_alert=True)


# ── Catch-all relay ───────────────────────────────────────────────────────────


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
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
                f"<i>Reply to this thread to respond. Use /resolve to close.</i>",
                parse_mode="HTML",
            )
            await queries.set_thread_msg_id(db_path, ticket_id, fwd.message_id)
        except Exception:
            logger.warning("Could not forward new ticket #%d to support chat", ticket_id)

        await message.answer(t("relay_new"))
        logger.info("Ticket #%d created by user %d", ticket_id, user.id)

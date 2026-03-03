"""Handlers for the support team: thread-based relay, /reply, /resolve, and inline button callbacks."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db import queries
from bot.states.admin import SupportReply

logger = logging.getLogger(__name__)
router = Router()


# ── Thread-based relay reply ──────────────────────────────────────────────────


@router.message(F.reply_to_message, F.text)
async def relay_support_reply(message: Message, db_path: str, support_chat_id: int) -> None:
    """Relay a support-agent reply in the support chat back to the user."""
    if message.chat.id != support_chat_id:
        return
    if not message.reply_to_message or not message.text:
        return

    replied_msg_id = message.reply_to_message.message_id
    ticket = await queries.get_ticket_by_forward_msg(db_path, replied_msg_id)
    if not ticket:
        return  # not a tracked thread

    agent_id = message.from_user.id if message.from_user else None
    await queries.append_message(db_path, ticket["id"], "support", agent_id, message.text)

    try:
        await message.bot.send_message(  # type: ignore[union-attr]
            ticket["user_id"],
            f"👨‍💼 <b>Support:</b> {message.text}",
            parse_mode="HTML",
        )
        logger.info("Relayed support reply for ticket #%d to user %d", ticket["id"], ticket["user_id"])
    except Exception:
        logger.warning(
            "Could not relay support reply for ticket #%d to user %d",
            ticket["id"],
            ticket["user_id"],
        )


# ── Command-based handlers ────────────────────────────────────────────────────


@router.message(Command("reply"))
async def cmd_reply(message: Message, db_path: str) -> None:
    """Usage: /reply <ticket_id> <message text>"""
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Usage: /reply <ticket_id> <message>")
        return

    ticket_id = int(parts[1])
    reply_body = parts[2]

    ticket = await queries.get_ticket(db_path, ticket_id)
    if not ticket:
        await message.answer(f"Ticket #{ticket_id} not found.")
        return

    agent_id = message.from_user.id  # type: ignore[union-attr]
    await queries.add_reply(db_path, ticket_id, agent_id, reply_body)

    await message.answer(f"Reply sent for ticket #{ticket_id}.")
    logger.info("Agent %d replied to ticket #%d", agent_id, ticket_id)

    try:
        await message.bot.send_message(  # type: ignore[union-attr]
            ticket["user_id"],
            f"📬 <b>Reply to your ticket #{ticket_id}</b>\n\n{reply_body}",
            parse_mode="HTML",
        )
    except Exception:
        logger.warning(
            "Could not notify user %d about reply to ticket #%d",
            ticket["user_id"],
            ticket_id,
        )


@router.message(Command("resolve"))
async def cmd_resolve(message: Message, db_path: str) -> None:
    """Usage: /resolve <ticket_id>"""
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /resolve <ticket_id>")
        return

    ticket_id = int(parts[1])
    updated = await queries.resolve_ticket(db_path, ticket_id)

    if not updated:
        await message.answer(
            f"Ticket #{ticket_id} not found or already resolved."
        )
        return

    ticket = await queries.get_ticket(db_path, ticket_id)
    await message.answer(f"Conversation #{ticket_id} marked as resolved.")
    logger.info(
        "Agent %d resolved ticket #%d",
        message.from_user.id,  # type: ignore[union-attr]
        ticket_id,
    )

    if ticket:
        try:
            await message.bot.send_message(  # type: ignore[union-attr]
                ticket["user_id"],
                f"✅ Your conversation has been resolved. "
                "Thank you for contacting support! Write any message to start a new one.",
            )
        except Exception:
            logger.warning(
                "Could not notify user %d about resolution of ticket #%d",
                ticket["user_id"],
                ticket_id,
            )


@router.message(Command("open_tickets"))
async def cmd_open_tickets(message: Message, db_path: str) -> None:
    """List all open conversations (support team only)."""
    tickets = await queries.get_open_tickets(db_path)

    if not tickets:
        await message.answer("No open conversations.")
        return

    lines = [f"<b>Open conversations ({len(tickets)}):</b>"]
    for t in tickets:
        username = f"@{t['username']}" if t["username"] else str(t["user_id"])
        lines.append(
            f"• <b>#{t['id']}</b> — {username} "
            f"(started {t['created_at'][:10]}) — /resolve {t['id']}"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


# ── Inline button callbacks ───────────────────────────────────────────────────


@router.callback_query(F.data.startswith("support:reply:"))
async def cb_support_reply_start(callback: CallbackQuery, state: FSMContext) -> None:
    ticket_id = int((callback.data or "").split(":")[2])
    await state.set_state(SupportReply.waiting_text)
    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer(  # type: ignore[union-attr]
        f"Send your reply for ticket #{ticket_id}:"
    )
    await callback.answer()


@router.message(SupportReply.waiting_text)
async def process_support_reply(
    message: Message, state: FSMContext, db_path: str
) -> None:
    if not message.text:
        await message.answer("Please send a text message.")
        return

    data = await state.get_data()
    ticket_id: int = data["ticket_id"]
    await state.clear()

    ticket = await queries.get_ticket(db_path, ticket_id)
    if not ticket:
        await message.answer(f"Ticket #{ticket_id} not found.")
        return

    agent_id = message.from_user.id  # type: ignore[union-attr]
    await queries.add_reply(db_path, ticket_id, agent_id, message.text)

    try:
        await message.bot.send_message(  # type: ignore[union-attr]
            ticket["user_id"],
            f"📬 <b>Reply to your ticket #{ticket_id}</b>\n\n{message.text}",
            parse_mode="HTML",
        )
        await message.answer(f"Reply sent for ticket #{ticket_id}.")
    except Exception:
        logger.warning(
            "Could not notify user %d about reply to ticket #%d",
            ticket["user_id"],
            ticket_id,
        )
        await message.answer(
            f"Reply recorded for ticket #{ticket_id}, but could not notify the user."
        )


@router.callback_query(F.data.startswith("support:resolve:"))
async def cb_support_resolve(callback: CallbackQuery, db_path: str) -> None:
    ticket_id = int((callback.data or "").split(":")[2])
    updated = await queries.resolve_ticket(db_path, ticket_id)

    if not updated:
        await callback.answer(
            f"Ticket #{ticket_id} not found or already resolved.", show_alert=True
        )
        return

    ticket = await queries.get_ticket(db_path, ticket_id)
    if ticket:
        try:
            await callback.bot.send_message(  # type: ignore[union-attr]
                ticket["user_id"],
                f"✅ Your ticket #{ticket_id} has been resolved. "
                "Thank you for contacting support!",
            )
        except Exception:
            logger.warning(
                "Could not notify user about resolution of ticket #%d", ticket_id
            )

    await callback.answer(f"Ticket #{ticket_id} resolved.", show_alert=True)
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"✅ Ticket #{ticket_id} has been resolved."
    )

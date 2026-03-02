"""Handlers for the support team: thread-based relay and /resolve."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import queries

logger = logging.getLogger(__name__)
router = Router()


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

    # Notify the user
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

"""Handlers for the support team: /reply and /resolve commands."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import queries

logger = logging.getLogger(__name__)
router = Router()


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

    if ticket["status"] == "resolved":
        await message.answer(f"Ticket #{ticket_id} is already resolved.")
        return

    agent_id = message.from_user.id  # type: ignore[union-attr]
    await queries.add_reply(db_path, ticket_id, agent_id, reply_body)

    await message.answer(f"Reply sent for ticket #{ticket_id}.")
    logger.info("Agent %d replied to ticket #%d", agent_id, ticket_id)

    # Notify the user who opened the ticket
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
    await message.answer(f"Ticket #{ticket_id} marked as resolved.")
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
                f"✅ Your ticket #{ticket_id} has been resolved. "
                "Thank you for contacting support!",
            )
        except Exception:
            logger.warning(
                "Could not notify user %d about resolution of ticket #%d",
                ticket["user_id"],
                ticket_id,
            )


@router.message(Command("open_tickets"))
async def cmd_open_tickets(message: Message, db_path: str) -> None:
    """List all open tickets (support team only)."""
    tickets = await queries.get_open_tickets(db_path)

    if not tickets:
        await message.answer("No open tickets.")
        return

    lines = [f"<b>Open tickets ({len(tickets)}):</b>"]
    for t in tickets:
        username = f"@{t['username']}" if t["username"] else str(t["user_id"])
        lines.append(
            f"• <b>#{t['id']}</b> — {t['subject']} [{username}] "
            f"(<i>/reply {t['id']} ...</i>)"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")

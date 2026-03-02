"""Shared handler utilities to eliminate repeated validation logic."""

from aiogram.types import Message

from bot.db.queries import get_ticket


async def parse_ticket_id(message: Message, min_parts: int, usage: str) -> int | None:
    """Parse and validate a ticket ID from message text.

    Returns the ticket ID as an int, or None if validation fails (after
    sending the appropriate error reply to the user).
    """
    parts = (message.text or "").split(maxsplit=min_parts)
    if len(parts) < min_parts:
        await message.answer(f"Usage: {usage}")
        return None
    ticket_id_str = parts[1]
    if not ticket_id_str.isdigit():
        await message.answer("ticket_id must be a number.")
        return None
    return int(ticket_id_str)


async def fetch_open_ticket(db_path: str, ticket_id: int, message: Message) -> dict | None:
    """Fetch a ticket and verify it exists and is open.

    Returns the ticket dict, or None if not found / not open (after
    sending the appropriate error reply to the user).
    """
    ticket = await get_ticket(db_path, ticket_id)
    if not ticket:
        await message.answer(f"Ticket #{ticket_id} not found.")
        return None
    if ticket["status"] != "open":
        await message.answer(f"Ticket #{ticket_id} is already {ticket['status']}.")
        return None
    return ticket

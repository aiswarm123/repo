"""Admin panel handlers — accessible only to configured admin users.

Filters (F.from_user.id.in_(admin_ids)) are applied in main.py after the
config is loaded, before this router is included in the dispatcher.
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db import queries
from bot.keyboards.admin import (
    admin_menu_keyboard,
    stats_keyboard,
    ticket_view_keyboard,
    tickets_list_keyboard,
)
from bot.states.admin import AdminBroadcast, AdminReply

logger = logging.getLogger(__name__)

PER_PAGE = 5

router = Router()


# ── /admin — Main menu ────────────────────────────────────────────────────────


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer("🛠 Admin Panel", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        "🛠 Admin Panel", reply_markup=admin_menu_keyboard()
    )
    await callback.answer()


# ── Tickets list ──────────────────────────────────────────────────────────────


async def _send_tickets_page(
    db_path: str,
    status: str,
    page: int,
    target: Message | CallbackQuery,
) -> None:
    counts = await queries.get_ticket_count_by_status(db_path)
    total = counts.get(status, 0)
    tickets = await queries.get_all_tickets(db_path, status, PER_PAGE, page * PER_PAGE)

    if not tickets:
        text = f"No {status} tickets."
    else:
        lines = [f"<b>Tickets ({status}) — page {page + 1}</b>"]
        for t in tickets:
            username = f"@{t['username']}" if t["username"] else str(t["user_id"])
            lines.append(
                f"<b>#{t['id']}</b> | {username} | {t['subject']} | {t['created_at'][:10]}"
            )
        text = "\n".join(lines)

    keyboard = tickets_list_keyboard(tickets, status, page, total, PER_PAGE)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.message.edit_text(  # type: ignore[union-attr]
            text, reply_markup=keyboard, parse_mode="HTML"
        )
        await target.answer()


@router.message(Command("tickets"))
async def cmd_tickets(message: Message, db_path: str) -> None:
    args = (message.text or "").split()
    status = args[1] if len(args) > 1 and args[1] in ("open", "resolved") else "open"
    await _send_tickets_page(db_path, status, 0, message)


@router.callback_query(F.data.startswith("admin:tickets:"))
async def cb_tickets(callback: CallbackQuery, db_path: str) -> None:
    parts = (callback.data or "").split(":")
    status = parts[2]
    page = int(parts[3])
    await _send_tickets_page(db_path, status, page, callback)


# ── Single ticket view ────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:view:"))
async def cb_view_ticket(callback: CallbackQuery, db_path: str) -> None:
    parts = (callback.data or "").split(":")
    ticket_id = int(parts[2])
    status = parts[3]
    page = int(parts[4])

    ticket = await queries.get_ticket(db_path, ticket_id)
    if not ticket:
        await callback.answer(f"Ticket #{ticket_id} not found.", show_alert=True)
        return

    username = f"@{ticket['username']}" if ticket["username"] else str(ticket["user_id"])
    text = (
        f"<b>Ticket #{ticket['id']}</b>\n"
        f"User: {username} (ID: {ticket['user_id']})\n"
        f"Subject: {ticket['subject']}\n"
        f"Status: {ticket['status']}\n"
        f"Created: {ticket['created_at']}\n"
    )
    if ticket["resolved_at"]:
        text += f"Resolved: {ticket['resolved_at']}\n"
    text += f"\n{ticket['body']}"

    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        reply_markup=ticket_view_keyboard(ticket_id, ticket["status"], page),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Reply flow ────────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:reply:"))
async def cb_reply_start(callback: CallbackQuery, state: FSMContext) -> None:
    ticket_id = int((callback.data or "").split(":")[2])
    await state.set_state(AdminReply.waiting_reply)
    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer(  # type: ignore[union-attr]
        f"Send your reply for ticket #{ticket_id}:"
    )
    await callback.answer()


@router.message(AdminReply.waiting_reply)
async def process_admin_reply(
    message: Message,
    state: FSMContext,
    db_path: str,
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
        await message.answer(f"Reply sent to user for ticket #{ticket_id}.")
    except Exception:
        logger.warning(
            "Could not notify user %d about reply to ticket #%d",
            ticket["user_id"],
            ticket_id,
        )
        await message.answer(
            f"Reply recorded for ticket #{ticket_id}, but could not notify the user."
        )


# ── Resolve via inline button ─────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:resolve:"))
async def cb_resolve_ticket(callback: CallbackQuery, db_path: str) -> None:
    ticket_id = int((callback.data or "").split(":")[2])
    updated = await queries.resolve_ticket(db_path, ticket_id)

    if not updated:
        await callback.answer(
            f"Ticket #{ticket_id} not found or already resolved.", show_alert=True
        )
        return

    ticket = await queries.get_ticket(db_path, ticket_id)
    try:
        if ticket:
            await callback.bot.send_message(  # type: ignore[union-attr]
                ticket["user_id"],
                f"✅ Your ticket #{ticket_id} has been resolved. "
                "Thank you for contacting support!",
            )
    except Exception:
        logger.warning("Could not notify user about resolution of ticket #%d", ticket_id)

    await callback.answer(f"Ticket #{ticket_id} resolved.", show_alert=True)
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"✅ Ticket #{ticket_id} has been resolved."
    )


# ── /stats ────────────────────────────────────────────────────────────────────


async def _build_stats_text(db_path: str) -> str:
    counts = await queries.get_ticket_count_by_status(db_path)
    user_ids = await queries.get_unique_user_ids(db_path)
    last_24h = await queries.get_last_24h_count(db_path)

    total = counts.get("total", 0)
    open_count = counts.get("open", 0)
    resolved_count = counts.get("resolved", 0)

    return (
        "📊 <b>Bot Statistics</b>\n"
        f"Total tickets: {total}\n"
        f"Open: {open_count}\n"
        f"Resolved: {resolved_count}\n"
        f"Users served: {len(user_ids)}\n"
        f"Last 24h: {last_24h} new tickets"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, db_path: str) -> None:
    await message.answer(await _build_stats_text(db_path), parse_mode="HTML")


@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery, db_path: str) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        await _build_stats_text(db_path),
        reply_markup=stats_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── /broadcast ────────────────────────────────────────────────────────────────


async def _do_broadcast(message: Message, db_path: str, text: str) -> None:
    user_ids = await queries.get_unique_user_ids(db_path)
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, text)  # type: ignore[union-attr]
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"Broadcast sent to {sent} users ({failed} failed).")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, db_path: str) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /broadcast <message>")
        return
    await _do_broadcast(message, db_path, parts[1])


@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminBroadcast.waiting_text)
    await callback.message.answer(  # type: ignore[union-attr]
        "Enter the broadcast message to send to all users:"
    )
    await callback.answer()


@router.message(AdminBroadcast.waiting_text)
async def process_broadcast(
    message: Message,
    state: FSMContext,
    db_path: str,
) -> None:
    if not message.text:
        await message.answer("Please send a text message.")
        return
    await state.clear()
    await _do_broadcast(message, db_path, message.text)


# ── /ban & /unban ─────────────────────────────────────────────────────────────


@router.message(Command("ban"))
async def cmd_ban(message: Message, db_path: str) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /ban <user_id>")
        return
    user_id = int(parts[1])
    await queries.ban_user(db_path, user_id)
    await message.answer(f"User {user_id} has been banned.")
    logger.info("Admin banned user %d", user_id)


@router.message(Command("unban"))
async def cmd_unban(message: Message, db_path: str) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /unban <user_id>")
        return
    user_id = int(parts[1])
    removed = await queries.unban_user(db_path, user_id)
    if removed:
        await message.answer(f"User {user_id} has been unbanned.")
        logger.info("Admin unbanned user %d", user_id)
    else:
        await message.answer(f"User {user_id} was not banned.")


@router.callback_query(F.data == "admin:ban")
async def cb_ban_prompt(callback: CallbackQuery) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "To ban a user send: /ban <user_id>\nTo unban: /unban <user_id>"
    )
    await callback.answer()

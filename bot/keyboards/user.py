from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Fixed button texts for reply keyboard routing
MENU_OPEN_TICKET = "🎫 Open Ticket"
MENU_MY_TICKETS = "📋 My Tickets"
MENU_LANGUAGE = "🌐 Language"
MENU_HELP = "❓ Help"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_OPEN_TICKET), KeyboardButton(text=MENU_MY_TICKETS)],
            [KeyboardButton(text=MENU_LANGUAGE), KeyboardButton(text=MENU_HELP)],
        ],
        resize_keyboard=True,
        persistent=True,
    )


def open_ticket_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎫 Open a Support Ticket", callback_data="ticket:open")]
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang:uk"),
            ]
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )


def confirm_ticket_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Submit", callback_data="ticket:submit"),
                InlineKeyboardButton(text="✏️ Edit", callback_data="ticket:edit"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"),
            ]
        ]
    )


def ticket_submitted_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 View Ticket",
                    callback_data=f"ticket:view:{ticket_id}",
                )
            ]
        ]
    )


def my_tickets_keyboard(tickets: list[dict]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for ticket in tickets:
        icon = "🟢" if ticket["status"] == "open" else "✅"
        subject = ticket.get("subject") or f"Ticket #{ticket['id']}"
        label = f"{icon} #{ticket['id']} — {subject[:35]}"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"ticket:view:{ticket['id']}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ticket_detail_keyboard(ticket_id: int, is_open: bool = True) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ticket:refresh:{ticket_id}")]
    ]
    if is_open:
        rows.append([
            InlineKeyboardButton(text="🗑 Close ticket", callback_data=f"ticket:close:{ticket_id}")
        ])
    rows.append([
        InlineKeyboardButton(text="← Back", callback_data="ticket:list")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎫 Tickets", callback_data="help:tickets"),
                InlineKeyboardButton(text="⚙️ Account", callback_data="help:account"),
                InlineKeyboardButton(text="💳 Billing", callback_data="help:billing"),
                InlineKeyboardButton(text="📞 Contact", callback_data="help:contact"),
            ]
        ]
    )

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def ticket_notification_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Reply", callback_data=f"support:reply:{ticket_id}"),
                InlineKeyboardButton(text="✅ Resolve", callback_data=f"support:resolve:{ticket_id}"),
            ]
        ]
    )

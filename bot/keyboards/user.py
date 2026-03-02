from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
        ]
    )


def ticket_submitted_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="View ticket status",
                    callback_data=f"status:{ticket_id}",
                )
            ]
        ]
    )

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 All Tickets", callback_data="admin:tickets:open:0"),
                InlineKeyboardButton(text="📊 Stats", callback_data="admin:stats"),
            ],
            [
                InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast"),
                InlineKeyboardButton(text="🚫 Ban User", callback_data="admin:ban"),
            ],
        ]
    )


def tickets_list_keyboard(
    tickets: list[dict],
    status: str,
    page: int,
    total: int,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []

    for t in tickets:
        buttons.append([
            InlineKeyboardButton(
                text=f"View #{t['id']}",
                callback_data=f"admin:view:{t['id']}:{status}:{page}",
            )
        ])

    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="← Prev", callback_data=f"admin:tickets:{status}:{page - 1}")
        )
    if (page + 1) * per_page < total:
        nav_row.append(
            InlineKeyboardButton(text="Next →", callback_data=f"admin:tickets:{status}:{page + 1}")
        )
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ticket_view_keyboard(ticket_id: int, status: str, page: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status == "open":
        rows.append([
            InlineKeyboardButton(text="Reply", callback_data=f"admin:reply:{ticket_id}"),
            InlineKeyboardButton(text="Resolve", callback_data=f"admin:resolve:{ticket_id}"),
        ])
    rows.append([
        InlineKeyboardButton(text="Back to list", callback_data=f"admin:tickets:{status}:{page}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Back", callback_data="admin:menu")]
        ]
    )

"""Message template functions to centralise notification text."""


def new_ticket_msg(ticket_id: int, username_display: str, subject: str, body: str) -> str:
    return (
        f"📩 <b>New ticket #{ticket_id}</b>\n"
        f"From: {username_display}\n"
        f"Subject: {subject}\n\n"
        f"{body}\n\n"
        f"Reply with: <code>/reply {ticket_id} &lt;message&gt;</code>\n"
        f"Resolve with: <code>/resolve {ticket_id}</code>"
    )


def support_reply_msg(ticket_id: int, subject: str, text: str) -> str:
    return f"📬 <b>Reply to your ticket #{ticket_id}</b>\n\n{text}"


def ticket_resolved_msg(ticket_id: int, subject: str, note: str) -> str:
    return (
        f"✅ Your ticket #{ticket_id} has been resolved. "
        "Thank you for contacting support!"
    )

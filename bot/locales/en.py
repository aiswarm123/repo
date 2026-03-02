"""English strings."""

STRINGS: dict[str, str] = {
    "start": (
        "Hi {name}! I'm the support bot.\n\n"
        "Just send me a message and I'll connect you with our support team.\n"
        "Use /mystatus to check your current conversation.\n"
        "Use /cancel to close your conversation."
    ),
    "help": (
        "How to reach support:\n"
        "• Send any message — it goes straight to the support team\n"
        "• /mystatus — view your current conversation\n"
        "• /cancel — close your conversation\n"
        "• /language — change language"
    ),
    "cancel_nothing": "You have no open conversation to cancel.",
    "cancelled": "Your conversation has been closed.",
    "relay_new": "✅ Your message has been sent to support. We'll reply here shortly.",
    "relay_sent": "✅ Message sent to support.",
    "mystatus_none": "You have no open conversation.",
    "mystatus_header": "Your current conversation:",
    "language_choose": "Choose your language:",
    "language_set": "Language updated!",
}

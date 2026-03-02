"""English strings."""

STRINGS: dict[str, str] = {
    "start": "Hi {name}! I'm the support bot.\n\nUse /ticket to open a new support ticket.\nUse /mystatus <ticket_id> to check a ticket's status.",
    "help": "Available commands:\n/ticket — open a support ticket\n/mystatus <id> — check ticket status\n/language — change language",
    "cancel_nothing": "Nothing to cancel.",
    "cancelled": "Cancelled.",
    "ticket_ask_subject": "Let's open a ticket. First, give it a short subject line.",
    "ticket_ask_body": "Got it. Now describe the issue in detail.",
    "ticket_subject_invalid": "Please send a text subject.",
    "ticket_body_invalid": "Please send a text description.",
    "ticket_submitted": "Ticket #{id} submitted! You'll be notified when our team responds.",
    "mystatus_none": "You have no open tickets.",
    "mystatus_header": "Your open tickets:",
    "language_choose": "Choose your language:",
    "language_set": "Language updated!",
}

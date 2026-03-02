"""Russian strings."""

STRINGS: dict[str, str] = {
    "start": "Привет, {name}! Я бот поддержки.\n\nИспользуйте /ticket для создания заявки.\nИспользуйте /mystatus <id> для проверки статуса заявки.",
    "help": "Доступные команды:\n/ticket — открыть заявку\n/mystatus <id> — проверить статус заявки\n/language — сменить язык",
    "cancel_nothing": "Нечего отменять.",
    "cancelled": "Отменено.",
    "ticket_ask_subject": "Создаём заявку. Сначала укажите краткую тему.",
    "ticket_ask_body": "Хорошо. Теперь подробно опишите проблему.",
    "ticket_subject_invalid": "Пожалуйста, отправьте текстовую тему.",
    "ticket_body_invalid": "Пожалуйста, отправьте текстовое описание.",
    "ticket_submitted": "Заявка #{id} отправлена! Мы уведомим вас, когда команда ответит.",
    "mystatus_none": "У вас нет открытых заявок.",
    "mystatus_header": "Ваши открытые заявки:",
    "language_choose": "Выберите язык:",
    "language_set": "Язык обновлён!",
}

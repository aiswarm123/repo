> 🇺🇦 Українська версія. [English](README.md)

# aiswarm — Telegram Support Bot

Готовий до production бот Telegram для заявок підтримки, побудований на **aiogram 3.x** та **aiosqlite**.

## Можливості

- `/ticket` — відкриває нову заявку підтримки через діалог з FSM
- `/mystatus <ticket_id>` — дозволяє користувачу перевірити статус своєї заявки
- `/reply <ticket_id> <message>` — агенти підтримки відповідають на заявку
- `/resolve <ticket_id>` — агенти підтримки закривають заявку
- `/open_tickets` — агенти підтримки переглядають усі відкриті заявки
- SQLite-персистентність через `aiosqlite`
- Повністю асинхронний; однопроцесний, не потребує зовнішнього брокера

## Швидкий старт

### 1. Клонування та налаштування

```bash
cp .env.example .env
# Відредагуйте .env — вкажіть BOT_TOKEN і SUPPORT_CHAT_ID
```

### 2. Локальний запуск (venv)

```bash
make install   # створює .venv та встановлює залежності
make run       # запускає бота
```

### 3. Запуск через Docker Compose

```bash
cp .env.example .env  # заповніть значення
docker compose up -d
```

Логи:

```bash
docker compose logs -f bot
```

## Конфігурація

| Змінна           | Обов'язкова | Опис                                                         |
|------------------|-------------|--------------------------------------------------------------|
| `BOT_TOKEN`      | Так         | Токен бота від [@BotFather](https://t.me/BotFather)          |
| `SUPPORT_CHAT_ID`| Так         | Ідентифікатор чату/групи Telegram, куди пересилаються заявки |
| `DATABASE_PATH`  | Ні          | Шлях до SQLite-файлу (за замовчуванням: `support.db`)        |

## Запуск тестів

```bash
make test
```

Потребує Python 3.11+ з підтримкою `venv`. Усі 8 тестів покривають шар `bot/db/queries.py`.

## Структура проекту

```
bot/
  main.py           # Точка входу — підключає бота, диспетчер та залежності
  config.py         # Завантажує конфігурацію з .env
  db/
    queries.py      # Асинхронний шар запитів до БД (aiosqlite)
  handlers/
    user.py         # /start, FSM /ticket, /mystatus
    support.py      # /reply, /resolve, /open_tickets
  states/
    ticket.py       # FSM-стани для створення заявки
  keyboards/
    user.py         # Вбудовані клавіатури
tests/
  test_queries.py   # pytest-asyncio тести для шару БД
Dockerfile
docker-compose.yml
Makefile
requirements.txt
requirements-dev.txt
.env.example
```

## Потік роботи бота

### Користувач створює заявку

```
User: /ticket
Bot:  "Please enter a short subject…"
User: My app keeps crashing
Bot:  "Now describe your issue in detail…"
User: It crashes whenever I tap the settings icon.
Bot:  "Ticket #1 submitted! Our team will get back to you shortly."
```

Чат підтримки отримує відформатоване сповіщення із попередньо заповненими командами `/reply` та `/resolve`.

### Агент підтримки відповідає

```
Agent: /reply 1 We are investigating — will update you soon.
Bot:   Forwards reply to the user who opened the ticket.
```

### Агент підтримки вирішує заявку

```
Agent: /resolve 1
Bot:   Marks ticket resolved and notifies the user.
```

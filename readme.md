# aiswarm — Telegram Support Bot

A production-ready Telegram support-ticket bot built with **aiogram 3.x** and **aiosqlite**.

## Features

- `/ticket` — opens a new support ticket via a guided FSM conversation
- `/mystatus <ticket_id>` — lets a user check the status of their ticket
- `/reply <ticket_id> <message>` — support agents reply to a ticket
- `/resolve <ticket_id>` — support agents close a ticket
- `/open_tickets` — support agents list all open tickets
- SQLite persistence via `aiosqlite`
- Fully async; single-process, no external broker required

## Quick Start

### 1. Clone & configure

```bash
cp .env.example .env
# Edit .env — set BOT_TOKEN and SUPPORT_CHAT_ID
```

### 2. Run locally (venv)

```bash
make install   # creates .venv and installs dependencies
make run       # starts the bot
```

### 3. Run with Docker Compose

```bash
cp .env.example .env  # fill in values
docker compose up -d
```

Logs:

```bash
docker compose logs -f bot
```

## Configuration

| Variable         | Required | Description                                              |
|------------------|----------|----------------------------------------------------------|
| `BOT_TOKEN`      | Yes      | Bot token from [@BotFather](https://t.me/BotFather)     |
| `SUPPORT_CHAT_ID`| Yes      | Telegram chat/group ID where new tickets are forwarded   |
| `DATABASE_PATH`  | No       | SQLite file path (default: `support.db`)                 |

## Running Tests

```bash
make test
```

Requires Python 3.11+ with `venv` support. All 8 tests cover the `bot/db/queries.py` layer.

## Project Structure

```
bot/
  main.py           # Entry point — wires bot, dispatcher, and dependencies
  config.py         # Loads .env configuration
  db/
    queries.py      # Async DB query layer (aiosqlite)
  handlers/
    user.py         # /start, /ticket FSM, /mystatus
    support.py      # /reply, /resolve, /open_tickets
  states/
    ticket.py       # FSM states for ticket creation
  keyboards/
    user.py         # Inline keyboards
tests/
  test_queries.py   # pytest-asyncio tests for the DB layer
Dockerfile
docker-compose.yml
Makefile
requirements.txt
requirements-dev.txt
.env.example
```

## Bot Flow

### User creates a ticket

```
User: /ticket
Bot:  "Please enter a short subject…"
User: My app keeps crashing
Bot:  "Now describe your issue in detail…"
User: It crashes whenever I tap the settings icon.
Bot:  "Ticket #1 submitted! Our team will get back to you shortly."
```

The support chat receives a formatted notification with `/reply` and `/resolve` commands pre-filled.

### Support agent replies

```
Agent: /reply 1 We are investigating — will update you soon.
Bot:   Forwards reply to the user who opened the ticket.
```

### Support agent resolves

```
Agent: /resolve 1
Bot:   Marks ticket resolved and notifies the user.
```

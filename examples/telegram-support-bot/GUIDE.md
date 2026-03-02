# Telegram Support Bot — User Guide

A step-by-step guide for everyone who interacts with the bot: end users opening tickets,
support agents answering them, and admins managing the deployment.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Configuration reference](#3-configuration-reference)
4. [End-user guide](#4-end-user-guide)
5. [Support team guide](#5-support-team-guide)
6. [Admin guide](#6-admin-guide)
7. [Troubleshooting](#7-troubleshooting)
8. [Updating the bot](#8-updating-the-bot)

---

## 1. Prerequisites

Before you start you will need:

- **Python 3.12+** (if running locally) **or Docker** (if running in a container)
- A **Telegram account**
- Access to **@BotFather** — the official Telegram bot that creates and manages bots
- A **dedicated Telegram group** that will act as the support inbox (the bot forwards
  every user ticket there)

---

## 2. Installation

### ✅ Option A — Local (Python)

1. **Clone or download the repository**

   ```bash
   git clone https://github.com/aiswarm123/repo.git
   cd repo/examples/telegram-support-bot
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Or, if you have `make`:

   ```bash
   make install
   ```

3. **Create your `.env` file**

   ```bash
   cp .env.example .env
   ```

   Open `.env` in any text editor and fill in the values (see
   [Section 3](#3-configuration-reference) for details).

4. **Start the bot**

   ```bash
   python main.py
   ```

   Or with `make`:

   ```bash
   make run
   ```

   You should see log lines like `Starting bot...` — the bot is now polling Telegram.

---

### ✅ Option B — Docker

1. **Create your `.env` file**

   ```bash
   cp .env.example .env
   ```

   Fill in the values (see [Section 3](#3-configuration-reference)).

2. **Build and start the container**

   ```bash
   make docker-up
   ```

   This runs `docker compose up -d --build` in the background.

3. **Check the logs**

   ```bash
   make docker-logs
   ```

   You should see `Starting bot...` in the output. Press `Ctrl+C` to stop following logs —
   the container keeps running.

4. **Stop the bot when needed**

   ```bash
   docker compose down
   ```

---

## 3. Configuration reference

All settings are read from a `.env` file (or real environment variables).

| Variable | Required | Default | Description & how to get it |
|---|---|---|---|
| `BOT_TOKEN` | **Yes** | — | Your bot's API token. Open **@BotFather** → `/newbot` → follow the prompts → copy the token it gives you (looks like `123456:ABC-DEF…`). |
| `SUPPORT_CHAT_ID` | **Yes** | — | The Telegram group ID that receives forwarded tickets. Add **@getidsbot** to your support group, send any message, and copy the **negative** number it reports (e.g. `-1001234567890`). |
| `DATABASE_PATH` | No | `support.db` | Path to the SQLite file where tickets are stored. Change this if you want the database somewhere specific (e.g. `/data/support.db`). |

### Getting your bot token step by step

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot`.
3. Enter a display name for the bot (e.g. `Acme Support`).
4. Enter a username ending in `bot` (e.g. `acme_support_bot`).
5. BotFather replies with the token — copy the entire string and paste it as `BOT_TOKEN`.

### Getting your support group ID

1. Create a new Telegram group (or use an existing one).
2. Add the bot itself as a member of that group.
3. Add **@getidsbot** to the group temporarily.
4. @getidsbot will post the group's ID — it will be a **negative** number (e.g. `-1001234567890`).
5. Copy that number as `SUPPORT_CHAT_ID`, then remove @getidsbot.

---

## 4. End-user guide

Users interact with the bot in a **private chat** — never in the support group.

### Starting the bot

Find the bot by its username and tap **Start**, or send `/start`.

```
User:  /start
Bot:   Welcome to Support Bot!

       Use /ticket to open a new support ticket.
       Use /mystatus <ticket_id> to check a ticket's status.
```

---

### 📋 Opening a ticket

The bot walks you through two steps: a short subject, then a detailed description.

```
User:  /ticket
Bot:   Please enter a short subject for your ticket:
       [Cancel]

User:  Can't log in

Bot:   Now describe your issue in detail:
       [Cancel]

User:  I enter my password and keep getting "Invalid credentials"
       even though I'm sure it's correct.

Bot:   Ticket #42 submitted! Our team will get back to you shortly.
       [View ticket status]
```

- Tap **Cancel** at any point to abort without creating a ticket.
- Tap **View ticket status** after submission to see the current status in a popup.

---

### Checking a ticket's status

Use `/mystatus <ticket_id>` with the number from the confirmation message.

```
User:  /mystatus 42

Bot:   Ticket #42
       Subject: Can't log in
       Status: open
       Created: 2026-03-01 14:05:32

       Replies:
       • Try resetting your password at example.com/reset
```

If the ticket has no replies yet, the **Replies** section is omitted.

> ⚠️ You can only view tickets you opened yourself. Trying to check someone else's
> ticket returns an error.

---

### Receiving a reply from the support team

When an agent replies to your ticket, the bot sends you a private message automatically —
you do not need to do anything.

```
Bot:   📬 Reply to your ticket #42

       Try resetting your password at example.com/reset
```

---

### Ticket resolved notification

When an agent marks your ticket as resolved, you receive:

```
Bot:   ✅ Your ticket #42 has been resolved.
       Thank you for contacting support!
```

---

## 5. Support team guide

Support agents work inside the **support group** that you set with `SUPPORT_CHAT_ID`.
The bot posts every new ticket there and provides commands to respond.

### ⚠️ Important: the bot must be a group member

The bot will not post tickets to the group unless it has been **added as a member**.
If tickets are not appearing, check this first (see [Troubleshooting](#7-troubleshooting)).

---

### Receiving a ticket

When a user submits a ticket the bot posts a message in the support group:

```
Bot:   📩 New ticket #42
       From: @alex123
       Subject: Can't log in

       I enter my password and keep getting "Invalid credentials"
       even though I'm sure it's correct.

       Reply with:   /reply 42 <message>
       Resolve with: /resolve 42
```

---

### Replying to a ticket

```
Agent: /reply 42 Try resetting your password at example.com/reset

Bot:   Reply sent for ticket #42.
```

The user receives the reply as a private message immediately. You can send multiple
replies to the same ticket.

> ⚠️ Replying to an already-resolved ticket is not allowed:
> ```
> Agent: /reply 42 One more tip
> Bot:   Ticket #42 is already resolved.
> ```

---

### Resolving a ticket

```
Agent: /resolve 42

Bot:   Ticket #42 marked as resolved.
```

The user receives a notification that their ticket has been resolved. Once resolved,
a ticket cannot be reopened via bot commands.

---

### Viewing all open tickets

```
Agent: /open_tickets

Bot:   Open tickets (3):
       • #41 — Login page crashes [@bob456] (/reply 41 ...)
       • #42 — Can't log in [@alex123] (/reply 42 ...)
       • #43 — Payment error [987654321] (/reply 43 ...)
```

Users without a public username are shown by their numeric Telegram ID.

---

## 6. Admin guide

The current version of the bot does not ship with dedicated admin commands. Admins
manage the deployment at the infrastructure level.

### Starting and stopping

```bash
# Local
make run            # start
Ctrl+C              # stop

# Docker
make docker-up      # start (background)
make docker-down    # stop
make docker-logs    # tail logs
```

### Inspecting the database

The bot uses a SQLite database (default: `support.db`). You can query it directly with
any SQLite client.

```bash
sqlite3 support.db

# List all open tickets
SELECT id, username, subject, created_at FROM tickets WHERE status = 'open';

# Show all replies for ticket #42
SELECT body, created_at FROM ticket_replies WHERE ticket_id = 42;

# Mark a ticket resolved manually
UPDATE tickets SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
WHERE id = 42;
```

### Changing configuration

1. Edit `.env`.
2. Restart the bot:

   ```bash
   # Local
   Ctrl+C
   make run

   # Docker
   make docker-down
   make docker-up
   ```

---

## 7. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Bot does not respond to any message | `BOT_TOKEN` is wrong or revoked | Re-copy the token from @BotFather (`/mybots` → select bot → **API Token**). |
| Tickets are not appearing in the support group | Bot is not a member of the group | Open the group, tap the group name → **Add Members** → search for your bot and add it. |
| `SUPPORT_CHAT_ID` error on startup | Value is missing or not a valid integer | The ID must be a **negative** number (e.g. `-1001234567890`). Re-run @getidsbot in the group. |
| "Ticket #X not found" when using `/mystatus` | Wrong ticket ID, or the database file is in a different location | Check `DATABASE_PATH` in `.env`. Make sure you are sending the right number from the confirmation message. |
| "You don't have permission to view that ticket" | Trying to view another user's ticket | Each user can only view their own tickets. |
| Bot starts but crashes immediately | Missing Python dependency | Run `pip install -r requirements.txt` again, or rebuild the Docker image with `make docker-up`. |
| Replies not reaching the user | User has blocked the bot | Nothing can be done — the bot logs a warning and continues. |

---

## 8. Updating the bot

### Local

```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
make run
```

### Docker

```bash
git pull
make docker-up      # rebuilds the image and restarts the container
```

The database is stored in a Docker **named volume** (`support-db`), so your ticket
history is preserved across image rebuilds.

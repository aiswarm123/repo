"""Async database query layer using aiosqlite."""

import aiosqlite


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    username    TEXT,
    subject     TEXT NOT NULL,
    body        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME
);

CREATE TABLE IF NOT EXISTS ticket_replies (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    agent_id   INTEGER NOT NULL,
    body       TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id  INTEGER PRIMARY KEY,
    language TEXT NOT NULL DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS banned_users (
    user_id   INTEGER PRIMARY KEY,
    banned_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db(db_path: str) -> None:
    """Create tables if they don't already exist."""
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()


async def create_ticket(
    db_path: str,
    user_id: int,
    username: str | None,
    subject: str,
    body: str,
) -> int:
    """Insert a new ticket and return its id."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO tickets (user_id, username, subject, body) VALUES (?, ?, ?, ?)",
            (user_id, username, subject, body),
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore[return-value]


async def get_ticket(db_path: str, ticket_id: int) -> dict | None:
    """Fetch a single ticket by id. Returns None if not found."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_open_tickets(db_path: str) -> list[dict]:
    """Return all tickets with status='open'."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE status = 'open' ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def resolve_ticket(db_path: str, ticket_id: int) -> bool:
    """Mark a ticket as resolved. Returns True if a row was updated."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "UPDATE tickets SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND status = 'open'",
            (ticket_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def add_reply(
    db_path: str,
    ticket_id: int,
    agent_id: int,
    body: str,
) -> int:
    """Insert a reply for a ticket and return its id."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO ticket_replies (ticket_id, agent_id, body) VALUES (?, ?, ?)",
            (ticket_id, agent_id, body),
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore[return-value]


async def get_replies(db_path: str, ticket_id: int) -> list[dict]:
    """Return all replies for a ticket ordered by creation time."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY created_at ASC",
            (ticket_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_user_language(db_path: str, user_id: int) -> str:
    """Return the stored language for a user, defaulting to 'en'."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT language FROM user_settings WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "en"


async def set_user_language(db_path: str, user_id: int, language: str) -> None:
    """Upsert the language preference for a user."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO user_settings (user_id, language) VALUES (?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET language = excluded.language",
            (user_id, language),
        )
        await db.commit()


# ── Admin queries ─────────────────────────────────────────────────────────────


async def get_all_tickets(
    db_path: str,
    status: str,
    limit: int,
    offset: int,
) -> list[dict]:
    """Return paginated tickets filtered by status."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_ticket_count_by_status(db_path: str) -> dict:
    """Return a dict with counts: total, open, resolved."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT status, COUNT(*) FROM tickets GROUP BY status"
        ) as cursor:
            rows = await cursor.fetchall()

    counts: dict[str, int] = {}
    for status, count in rows:
        counts[status] = count
    counts["total"] = sum(counts.values())
    return counts


async def get_unique_user_ids(db_path: str) -> list[int]:
    """Return list of unique user_ids from the tickets table."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT DISTINCT user_id FROM tickets") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_last_24h_count(db_path: str) -> int:
    """Return count of tickets created in the last 24 hours."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM tickets WHERE created_at >= datetime('now', '-1 day')"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def ban_user(db_path: str, user_id: int) -> None:
    """Add a user to the banned_users table (idempotent)."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,)
        )
        await db.commit()


async def unban_user(db_path: str, user_id: int) -> bool:
    """Remove a user from the banned_users table. Returns True if they were banned."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "DELETE FROM banned_users WHERE user_id = ?", (user_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def is_banned(db_path: str, user_id: int) -> bool:
    """Return True if the user is in the banned_users table."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone() is not None

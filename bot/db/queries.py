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

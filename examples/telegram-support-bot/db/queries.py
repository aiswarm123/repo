"""Async database query functions for the Telegram support bot."""
import aiosqlite


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    forward_msg_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    message TEXT NOT NULL,
    from_admin INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db(db: aiosqlite.Connection) -> None:
    """Create tables if they don't exist."""
    await db.executescript(CREATE_TABLES_SQL)
    await db.commit()


async def create_ticket(db: aiosqlite.Connection, user_id: int, message: str) -> int:
    """Insert a new support ticket and return its ID."""
    cursor = await db.execute(
        "INSERT INTO tickets (user_id, message, status) VALUES (?, ?, 'open')",
        (user_id, message),
    )
    await db.commit()
    return cursor.lastrowid


async def get_ticket(db: aiosqlite.Connection, ticket_id: int) -> dict | None:
    """Return the ticket row as a dict, or None if not found."""
    db.row_factory = aiosqlite.Row
    cursor = await db.execute(
        "SELECT * FROM tickets WHERE id = ?",
        (ticket_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


async def get_open_tickets(db: aiosqlite.Connection, user_id: int) -> list[dict]:
    """Return all open tickets belonging to *user_id*."""
    db.row_factory = aiosqlite.Row
    cursor = await db.execute(
        "SELECT * FROM tickets WHERE user_id = ? AND status = 'open'",
        (user_id,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def resolve_ticket(db: aiosqlite.Connection, ticket_id: int) -> None:
    """Set a ticket's status to 'resolved'."""
    await db.execute(
        "UPDATE tickets SET status = 'resolved' WHERE id = ?",
        (ticket_id,),
    )
    await db.commit()


async def add_reply(
    db: aiosqlite.Connection,
    ticket_id: int,
    message: str,
    from_admin: bool = False,
) -> int:
    """Persist a reply to a ticket and return the new reply ID."""
    cursor = await db.execute(
        "INSERT INTO replies (ticket_id, message, from_admin) VALUES (?, ?, ?)",
        (ticket_id, message, int(from_admin)),
    )
    await db.commit()
    return cursor.lastrowid


async def update_forward_msg(
    db: aiosqlite.Connection, ticket_id: int, forward_msg_id: int
) -> None:
    """Store the Telegram message ID used to forward the ticket to admins."""
    await db.execute(
        "UPDATE tickets SET forward_msg_id = ? WHERE id = ?",
        (forward_msg_id, ticket_id),
    )
    await db.commit()

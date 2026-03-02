"""pytest-asyncio tests for db/queries.py using an in-memory SQLite database."""
import sys
import os

import aiosqlite
import pytest

# Allow importing from the parent package without installing it.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.queries import (
    init_db,
    create_ticket,
    get_ticket,
    get_open_tickets,
    resolve_ticket,
    add_reply,
    update_forward_msg,
)


@pytest.fixture
async def db():
    """Provide a fresh in-memory SQLite connection with schema already applied."""
    async with aiosqlite.connect(":memory:") as connection:
        await init_db(connection)
        yield connection


# ---------------------------------------------------------------------------
# create_ticket
# ---------------------------------------------------------------------------


async def test_create_ticket_returns_int(db):
    ticket_id = await create_ticket(db, user_id=1, message="Hello")
    assert isinstance(ticket_id, int)
    assert ticket_id > 0


async def test_create_ticket_row_exists(db):
    ticket_id = await create_ticket(db, user_id=1, message="Hello")
    row = await get_ticket(db, ticket_id)
    assert row is not None
    assert row["id"] == ticket_id
    assert row["user_id"] == 1
    assert row["message"] == "Hello"
    assert row["status"] == "open"


# ---------------------------------------------------------------------------
# get_ticket
# ---------------------------------------------------------------------------


async def test_get_ticket_returns_correct_dict(db):
    ticket_id = await create_ticket(db, user_id=42, message="Need help")
    ticket = await get_ticket(db, ticket_id)
    assert ticket["id"] == ticket_id
    assert ticket["user_id"] == 42
    assert ticket["message"] == "Need help"


async def test_get_ticket_returns_none_for_missing_id(db):
    result = await get_ticket(db, ticket_id=99999)
    assert result is None


# ---------------------------------------------------------------------------
# get_open_tickets
# ---------------------------------------------------------------------------


async def test_get_open_tickets_only_returns_open(db):
    uid = 7
    open_id = await create_ticket(db, user_id=uid, message="Open one")
    closed_id = await create_ticket(db, user_id=uid, message="Closed one")
    await resolve_ticket(db, closed_id)

    open_tickets = await get_open_tickets(db, user_id=uid)
    ids = [t["id"] for t in open_tickets]
    assert open_id in ids
    assert closed_id not in ids


async def test_get_open_tickets_only_returns_for_right_user(db):
    await create_ticket(db, user_id=1, message="User 1 ticket")
    uid2_id = await create_ticket(db, user_id=2, message="User 2 ticket")

    tickets = await get_open_tickets(db, user_id=2)
    assert len(tickets) == 1
    assert tickets[0]["id"] == uid2_id


async def test_get_open_tickets_empty_when_none(db):
    tickets = await get_open_tickets(db, user_id=999)
    assert tickets == []


# ---------------------------------------------------------------------------
# resolve_ticket
# ---------------------------------------------------------------------------


async def test_resolve_ticket_changes_status(db):
    ticket_id = await create_ticket(db, user_id=1, message="Fix this")
    await resolve_ticket(db, ticket_id)

    ticket = await get_ticket(db, ticket_id)
    assert ticket["status"] == "resolved"


async def test_resolve_ticket_does_not_appear_in_open_tickets(db):
    uid = 5
    ticket_id = await create_ticket(db, user_id=uid, message="Will be resolved")
    await resolve_ticket(db, ticket_id)

    open_tickets = await get_open_tickets(db, user_id=uid)
    assert all(t["id"] != ticket_id for t in open_tickets)


# ---------------------------------------------------------------------------
# add_reply
# ---------------------------------------------------------------------------


async def test_add_reply_persists_row(db):
    ticket_id = await create_ticket(db, user_id=1, message="Question")
    reply_id = await add_reply(db, ticket_id=ticket_id, message="Answer", from_admin=True)

    assert isinstance(reply_id, int)
    assert reply_id > 0

    cursor = await db.execute(
        "SELECT * FROM replies WHERE id = ?", (reply_id,)
    )
    db.row_factory = aiosqlite.Row
    row = await cursor.fetchone()
    assert row is not None


async def test_add_reply_multiple_replies(db):
    ticket_id = await create_ticket(db, user_id=1, message="Question")
    id1 = await add_reply(db, ticket_id=ticket_id, message="First")
    id2 = await add_reply(db, ticket_id=ticket_id, message="Second")

    assert id1 != id2

    cursor = await db.execute(
        "SELECT COUNT(*) FROM replies WHERE ticket_id = ?", (ticket_id,)
    )
    (count,) = await cursor.fetchone()
    assert count == 2


# ---------------------------------------------------------------------------
# update_forward_msg
# ---------------------------------------------------------------------------


async def test_update_forward_msg_sets_column(db):
    ticket_id = await create_ticket(db, user_id=1, message="Forward me")
    await update_forward_msg(db, ticket_id=ticket_id, forward_msg_id=12345)

    ticket = await get_ticket(db, ticket_id)
    assert ticket["forward_msg_id"] == 12345


async def test_update_forward_msg_can_be_overwritten(db):
    ticket_id = await create_ticket(db, user_id=1, message="Forward me")
    await update_forward_msg(db, ticket_id=ticket_id, forward_msg_id=111)
    await update_forward_msg(db, ticket_id=ticket_id, forward_msg_id=999)

    ticket = await get_ticket(db, ticket_id)
    assert ticket["forward_msg_id"] == 999

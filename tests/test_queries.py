"""Tests for bot/db/queries.py using an in-memory SQLite database."""

import pytest
import pytest_asyncio

from bot.db.queries import (
    add_reply,
    create_ticket,
    get_open_tickets,
    get_replies,
    get_ticket,
    init_db,
    resolve_ticket,
)

# Use a shared in-memory database path for all tests.
# aiosqlite opens a new connection per call, so we use a file-based temp DB.


@pytest_asyncio.fixture
async def db(tmp_path):
    """Yield an initialised temporary SQLite database path."""
    path = str(tmp_path / "test.db")
    await init_db(path)
    return path


@pytest.mark.asyncio
async def test_create_and_get_ticket(db):
    """Creating a ticket returns a positive id and the ticket is retrievable."""
    ticket_id = await create_ticket(db, user_id=1, username="alice", subject="Help", body="I need help")
    assert ticket_id > 0

    ticket = await get_ticket(db, ticket_id)
    assert ticket is not None
    assert ticket["subject"] == "Help"
    assert ticket["body"] == "I need help"
    assert ticket["status"] == "open"
    assert ticket["user_id"] == 1
    assert ticket["username"] == "alice"


@pytest.mark.asyncio
async def test_get_ticket_not_found(db):
    """get_ticket returns None for a non-existent ticket id."""
    result = await get_ticket(db, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_get_open_tickets(db):
    """get_open_tickets returns only tickets with status='open'."""
    id1 = await create_ticket(db, user_id=1, username="alice", subject="A", body="body a")
    id2 = await create_ticket(db, user_id=2, username="bob", subject="B", body="body b")

    open_tickets = await get_open_tickets(db)
    ids = [t["id"] for t in open_tickets]
    assert id1 in ids
    assert id2 in ids

    # Resolve one ticket and verify it no longer appears
    await resolve_ticket(db, id1)
    open_tickets_after = await get_open_tickets(db)
    ids_after = [t["id"] for t in open_tickets_after]
    assert id1 not in ids_after
    assert id2 in ids_after


@pytest.mark.asyncio
async def test_resolve_ticket(db):
    """resolve_ticket marks the ticket as resolved and returns True."""
    ticket_id = await create_ticket(db, user_id=3, username=None, subject="Crash", body="App crashed")

    result = await resolve_ticket(db, ticket_id)
    assert result is True

    ticket = await get_ticket(db, ticket_id)
    assert ticket is not None
    assert ticket["status"] == "resolved"
    assert ticket["resolved_at"] is not None


@pytest.mark.asyncio
async def test_resolve_already_resolved(db):
    """resolve_ticket returns False when the ticket is already resolved."""
    ticket_id = await create_ticket(db, user_id=4, username="carol", subject="X", body="Y")
    await resolve_ticket(db, ticket_id)

    result = await resolve_ticket(db, ticket_id)
    assert result is False


@pytest.mark.asyncio
async def test_add_and_get_replies(db):
    """Replies can be added to a ticket and retrieved in order."""
    ticket_id = await create_ticket(db, user_id=5, username="dave", subject="Q", body="Question")

    reply_id1 = await add_reply(db, ticket_id, agent_id=100, body="First reply")
    reply_id2 = await add_reply(db, ticket_id, agent_id=101, body="Second reply")

    assert reply_id1 > 0
    assert reply_id2 > reply_id1

    replies = await get_replies(db, ticket_id)
    assert len(replies) == 2
    assert replies[0]["body"] == "First reply"
    assert replies[1]["body"] == "Second reply"
    assert replies[0]["agent_id"] == 100


@pytest.mark.asyncio
async def test_get_replies_empty(db):
    """get_replies returns an empty list when no replies exist."""
    ticket_id = await create_ticket(db, user_id=6, username=None, subject="Lonely", body="No replies")
    replies = await get_replies(db, ticket_id)
    assert replies == []


@pytest.mark.asyncio
async def test_multiple_tickets_independent(db):
    """Tickets are independent — resolving one does not affect others."""
    id1 = await create_ticket(db, user_id=7, username="eve", subject="S1", body="B1")
    id2 = await create_ticket(db, user_id=8, username="frank", subject="S2", body="B2")

    await resolve_ticket(db, id1)

    ticket2 = await get_ticket(db, id2)
    assert ticket2 is not None
    assert ticket2["status"] == "open"

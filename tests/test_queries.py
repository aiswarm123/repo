"""Tests for bot/db/queries.py using an in-memory SQLite database."""

import pytest
import pytest_asyncio

from bot.db.queries import (
    append_message,
    create_ticket,
    get_messages,
    get_open_ticket_by_user,
    get_open_tickets,
    get_ticket,
    get_ticket_by_forward_msg,
    init_db,
    resolve_ticket,
    set_thread_msg_id,
)


@pytest_asyncio.fixture
async def db(tmp_path):
    """Yield an initialised temporary SQLite database path."""
    path = str(tmp_path / "test.db")
    await init_db(path)
    return path


@pytest.mark.asyncio
async def test_create_and_get_ticket(db):
    """Creating a ticket returns a positive id and the ticket is retrievable."""
    ticket_id = await create_ticket(db, user_id=1, username="alice")
    assert ticket_id > 0

    ticket = await get_ticket(db, ticket_id)
    assert ticket is not None
    assert ticket["status"] == "open"
    assert ticket["user_id"] == 1
    assert ticket["username"] == "alice"


@pytest.mark.asyncio
async def test_get_ticket_not_found(db):
    """get_ticket returns None for a non-existent ticket id."""
    result = await get_ticket(db, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_set_thread_msg_id(db):
    """set_thread_msg_id stores forward_msg and thread_msg_id."""
    ticket_id = await create_ticket(db, user_id=1, username="alice")
    await set_thread_msg_id(db, ticket_id, 42)

    ticket = await get_ticket(db, ticket_id)
    assert ticket is not None
    assert ticket["forward_msg"] == 42
    assert ticket["thread_msg_id"] == 42


@pytest.mark.asyncio
async def test_get_open_ticket_by_user(db):
    """get_open_ticket_by_user returns the latest open ticket for a user."""
    id1 = await create_ticket(db, user_id=10, username="bob")
    ticket = await get_open_ticket_by_user(db, 10)
    assert ticket is not None
    assert ticket["id"] == id1

    await resolve_ticket(db, id1)
    ticket_after = await get_open_ticket_by_user(db, 10)
    assert ticket_after is None


@pytest.mark.asyncio
async def test_get_ticket_by_forward_msg(db):
    """get_ticket_by_forward_msg finds the ticket using the support-chat anchor ID."""
    ticket_id = await create_ticket(db, user_id=5, username="carol")
    await set_thread_msg_id(db, ticket_id, 999)

    found = await get_ticket_by_forward_msg(db, 999)
    assert found is not None
    assert found["id"] == ticket_id

    not_found = await get_ticket_by_forward_msg(db, 1234)
    assert not_found is None


@pytest.mark.asyncio
async def test_get_open_tickets(db):
    """get_open_tickets returns only tickets with status='open'."""
    id1 = await create_ticket(db, user_id=1, username="alice")
    id2 = await create_ticket(db, user_id=2, username="bob")

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
    ticket_id = await create_ticket(db, user_id=3, username=None)

    result = await resolve_ticket(db, ticket_id)
    assert result is True

    ticket = await get_ticket(db, ticket_id)
    assert ticket is not None
    assert ticket["status"] == "resolved"
    assert ticket["resolved_at"] is not None


@pytest.mark.asyncio
async def test_resolve_already_resolved(db):
    """resolve_ticket returns False when the ticket is already resolved."""
    ticket_id = await create_ticket(db, user_id=4, username="carol")
    await resolve_ticket(db, ticket_id)

    result = await resolve_ticket(db, ticket_id)
    assert result is False


@pytest.mark.asyncio
async def test_append_and_get_messages(db):
    """Messages can be appended to a ticket and retrieved in order."""
    ticket_id = await create_ticket(db, user_id=5, username="dave")

    await append_message(db, ticket_id, "user", 5, "Hello, I need help")
    await append_message(db, ticket_id, "support", 100, "Sure, what's the issue?")

    msgs = await get_messages(db, ticket_id)
    assert len(msgs) == 2
    assert msgs[0]["direction"] == "user"
    assert msgs[0]["text"] == "Hello, I need help"
    assert msgs[1]["direction"] == "support"
    assert msgs[1]["text"] == "Sure, what's the issue?"
    assert msgs[0]["sender_id"] == 5
    assert msgs[1]["sender_id"] == 100


@pytest.mark.asyncio
async def test_get_messages_empty(db):
    """get_messages returns an empty list when no messages exist."""
    ticket_id = await create_ticket(db, user_id=6, username=None)
    msgs = await get_messages(db, ticket_id)
    assert msgs == []


@pytest.mark.asyncio
async def test_multiple_tickets_independent(db):
    """Tickets are independent — resolving one does not affect others."""
    id1 = await create_ticket(db, user_id=7, username="eve")
    id2 = await create_ticket(db, user_id=8, username="frank")

    await resolve_ticket(db, id1)

    ticket2 = await get_ticket(db, id2)
    assert ticket2 is not None
    assert ticket2["status"] == "open"

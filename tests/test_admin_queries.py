"""Tests for admin-specific DB queries in bot/db/queries.py."""

import pytest
import pytest_asyncio

from bot.db.queries import (
    ban_user,
    create_ticket,
    get_all_tickets,
    get_last_24h_count,
    get_ticket_count_by_status,
    get_unique_user_ids,
    init_db,
    is_banned,
    resolve_ticket,
    unban_user,
)


@pytest_asyncio.fixture
async def db(tmp_path):
    """Yield an initialised temporary SQLite database path."""
    path = str(tmp_path / "test.db")
    await init_db(path)
    return path


@pytest.mark.asyncio
async def test_get_all_tickets_paginated(db):
    """get_all_tickets returns correct pages."""
    for i in range(7):
        await create_ticket(db, user_id=i, username=f"user{i}", subject=f"S{i}", body="body")

    page1 = await get_all_tickets(db, "open", limit=5, offset=0)
    assert len(page1) == 5

    page2 = await get_all_tickets(db, "open", limit=5, offset=5)
    assert len(page2) == 2


@pytest.mark.asyncio
async def test_get_all_tickets_status_filter(db):
    """get_all_tickets filters by status correctly."""
    id1 = await create_ticket(db, user_id=1, username="a", subject="S1", body="B1")
    await create_ticket(db, user_id=2, username="b", subject="S2", body="B2")
    await resolve_ticket(db, id1)

    open_tickets = await get_all_tickets(db, "open", limit=10, offset=0)
    resolved_tickets = await get_all_tickets(db, "resolved", limit=10, offset=0)

    assert len(open_tickets) == 1
    assert len(resolved_tickets) == 1
    assert open_tickets[0]["subject"] == "S2"
    assert resolved_tickets[0]["subject"] == "S1"


@pytest.mark.asyncio
async def test_get_ticket_count_by_status(db):
    """get_ticket_count_by_status returns correct counts."""
    id1 = await create_ticket(db, user_id=1, username="a", subject="S1", body="B1")
    await create_ticket(db, user_id=2, username="b", subject="S2", body="B2")
    await resolve_ticket(db, id1)

    counts = await get_ticket_count_by_status(db)
    assert counts["open"] == 1
    assert counts["resolved"] == 1
    assert counts["total"] == 2


@pytest.mark.asyncio
async def test_get_ticket_count_empty_db(db):
    """get_ticket_count_by_status returns zeros for an empty database."""
    counts = await get_ticket_count_by_status(db)
    assert counts.get("open", 0) == 0
    assert counts.get("resolved", 0) == 0
    assert counts.get("total", 0) == 0


@pytest.mark.asyncio
async def test_get_unique_user_ids(db):
    """get_unique_user_ids returns distinct user IDs only."""
    await create_ticket(db, user_id=10, username="x", subject="S1", body="B1")
    await create_ticket(db, user_id=10, username="x", subject="S2", body="B2")
    await create_ticket(db, user_id=20, username="y", subject="S3", body="B3")

    user_ids = await get_unique_user_ids(db)
    assert set(user_ids) == {10, 20}
    assert len(user_ids) == 2


@pytest.mark.asyncio
async def test_get_last_24h_count(db):
    """Newly created tickets are counted in the last 24h window."""
    await create_ticket(db, user_id=1, username="u", subject="S", body="B")
    count = await get_last_24h_count(db)
    assert count >= 1


@pytest.mark.asyncio
async def test_ban_user(db):
    """ban_user marks a user as banned."""
    assert not await is_banned(db, 42)
    await ban_user(db, 42)
    assert await is_banned(db, 42)


@pytest.mark.asyncio
async def test_ban_user_idempotent(db):
    """Banning the same user twice does not raise an error."""
    await ban_user(db, 99)
    await ban_user(db, 99)  # should not raise
    assert await is_banned(db, 99)


@pytest.mark.asyncio
async def test_unban_user(db):
    """unban_user removes the ban and returns True."""
    await ban_user(db, 42)
    result = await unban_user(db, 42)
    assert result is True
    assert not await is_banned(db, 42)


@pytest.mark.asyncio
async def test_unban_not_banned(db):
    """unban_user returns False when the user was not banned."""
    result = await unban_user(db, 999)
    assert result is False


@pytest.mark.asyncio
async def test_is_banned_false_for_new_user(db):
    """is_banned returns False for users never banned."""
    assert not await is_banned(db, 1234567)

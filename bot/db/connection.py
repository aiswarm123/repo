"""Shared DB connection helpers to eliminate aiosqlite boilerplate."""

from contextlib import asynccontextmanager

import aiosqlite


@asynccontextmanager
async def get_db(db_path: str):
    """Open an aiosqlite connection with row_factory pre-configured."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def execute_write(db_path: str, query: str, params: tuple = ()) -> int | None:
    """Execute a write query, commit, and return lastrowid."""
    async with get_db(db_path) as db:
        cur = await db.execute(query, params)
        await db.commit()
        return cur.lastrowid

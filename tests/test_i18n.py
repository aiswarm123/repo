"""Tests for i18n locale loading and user_settings DB queries."""

import pytest
import pytest_asyncio

from bot.db.queries import get_user_language, init_db, set_user_language
from bot.locales import SUPPORTED_LANGUAGES, get_text, make_t
from bot.locales import en, ru, uk


# ---------------------------------------------------------------------------
# Locale consistency tests
# ---------------------------------------------------------------------------

def test_all_locales_have_same_keys():
    """Every locale file must define exactly the same set of keys."""
    en_keys = set(en.STRINGS.keys())
    assert set(ru.STRINGS.keys()) == en_keys, "ru.STRINGS keys differ from en.STRINGS"
    assert set(uk.STRINGS.keys()) == en_keys, "uk.STRINGS keys differ from en.STRINGS"


def test_supported_languages_list():
    assert set(SUPPORTED_LANGUAGES) == {"en", "ru", "uk"}


def test_get_text_returns_english_for_unknown_lang():
    result = get_text("language_set", "fr")
    assert result == en.STRINGS["language_set"]


def test_get_text_returns_key_for_missing_key():
    result = get_text("nonexistent_key", "en")
    assert result == "nonexistent_key"


def test_get_text_russian():
    result = get_text("language_set", "ru")
    assert result == ru.STRINGS["language_set"]


def test_get_text_ukrainian():
    result = get_text("language_set", "uk")
    assert result == uk.STRINGS["language_set"]


def test_make_t_callable():
    t = make_t("ru")
    assert callable(t)
    assert t("language_set") == ru.STRINGS["language_set"]


def test_make_t_english():
    t = make_t("en")
    assert t("cancelled") == en.STRINGS["cancelled"]


# ---------------------------------------------------------------------------
# user_settings DB query tests
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db(tmp_path):
    path = str(tmp_path / "test_i18n.db")
    await init_db(path)
    return path


@pytest.mark.asyncio
async def test_get_user_language_default(db):
    """Unset user defaults to 'en'."""
    lang = await get_user_language(db, user_id=42)
    assert lang == "en"


@pytest.mark.asyncio
async def test_set_and_get_user_language(db):
    await set_user_language(db, user_id=1, language="ru")
    lang = await get_user_language(db, user_id=1)
    assert lang == "ru"


@pytest.mark.asyncio
async def test_set_user_language_upsert(db):
    """set_user_language should update an existing preference."""
    await set_user_language(db, user_id=2, language="ru")
    await set_user_language(db, user_id=2, language="uk")
    lang = await get_user_language(db, user_id=2)
    assert lang == "uk"


@pytest.mark.asyncio
async def test_set_user_language_multiple_users(db):
    await set_user_language(db, user_id=10, language="ru")
    await set_user_language(db, user_id=11, language="uk")

    assert await get_user_language(db, user_id=10) == "ru"
    assert await get_user_language(db, user_id=11) == "uk"
    assert await get_user_language(db, user_id=99) == "en"

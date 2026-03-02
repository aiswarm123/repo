"""Locale helpers for the support bot."""

from typing import Callable

from bot.locales import en, ru, uk

_LOCALES: dict[str, dict[str, str]] = {
    "en": en.STRINGS,
    "ru": ru.STRINGS,
    "uk": uk.STRINGS,
}

SUPPORTED_LANGUAGES = list(_LOCALES.keys())


def get_text(key: str, lang: str) -> str:
    """Return translated string for key in given language, falling back to English."""
    strings = _LOCALES.get(lang, _LOCALES["en"])
    return strings.get(key, _LOCALES["en"].get(key, key))


def make_t(lang: str) -> Callable[[str], str]:
    """Return a translation callable bound to the given language."""
    def t(key: str) -> str:
        return get_text(key, lang)
    return t

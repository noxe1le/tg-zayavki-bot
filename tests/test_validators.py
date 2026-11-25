import pytest

from app.validators import clean_comment, clean_name, normalize_phone


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+7 900 123-45-67", "+79001234567"),
        ("8 (900) 1234567", "+79001234567"),
        ("+79001234567", "+79001234567"),
        ("9001234567", "+79001234567"),
    ],
)
def test_phone_ok(raw: str, expected: str) -> None:
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "123", "не телефон", "+7 900 123-45-6"])
def test_phone_bad(raw: str) -> None:
    assert normalize_phone(raw) is None


def test_name_strips_spaces() -> None:
    assert clean_name("  Иван   Петров ") == "Иван Петров"


@pytest.mark.parametrize("raw", ["", "Я", "Иван2", "а" * 41])
def test_name_bad(raw: str) -> None:
    assert clean_name(raw) is None


def test_comment_short() -> None:
    assert clean_comment("нужен бот") is None


def test_comment_ok() -> None:
    assert clean_comment("  нужен   парсер цен с сайта  ") == "нужен парсер цен с сайта"


def test_comment_truncated() -> None:
    assert len(clean_comment("а" * 900) or "") == 600

import phonenumbers

MAX_NAME_LEN = 40
MAX_COMMENT_LEN = 600


def normalize_phone(raw: str) -> str | None:
    """Приводит номер к E.164. Возвращает None, если номер невалидный."""
    cleaned = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    try:
        parsed = phonenumbers.parse(cleaned, "RU")
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def clean_name(raw: str) -> str | None:
    name = " ".join(raw.split())
    if not 2 <= len(name) <= MAX_NAME_LEN:
        return None
    if any(ch.isdigit() for ch in name):
        return None
    return name


def clean_comment(raw: str) -> str | None:
    text = " ".join(raw.split())
    if len(text) < 10:
        return None
    return text[:MAX_COMMENT_LEN]

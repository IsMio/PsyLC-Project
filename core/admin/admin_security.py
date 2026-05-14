import json
from typing import Iterable, List, Sequence


def parse_roles(raw_roles: object) -> List[str]:
    if raw_roles is None:
        return []
    if isinstance(raw_roles, list):
        return [str(role).strip() for role in raw_roles if str(role).strip()]
    if isinstance(raw_roles, tuple):
        return [str(role).strip() for role in raw_roles if str(role).strip()]

    text = str(raw_roles).strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        return [str(role).strip() for role in parsed if str(role).strip()]
    if isinstance(parsed, str) and parsed.strip():
        return [parsed.strip()]

    if "," in text:
        return [item.strip() for item in text.split(",") if item.strip()]
    return [text]


def has_role(raw_roles: object, expected_role: str) -> bool:
    return expected_role in parse_roles(raw_roles)


def serialize_roles(roles: Sequence[str] | Iterable[str]) -> str:
    normalized = [str(role).strip() for role in roles if str(role).strip()]
    return json.dumps(normalized, ensure_ascii=False)

from datetime import datetime, timedelta
from typing import Any

_store: dict[str, tuple[Any, datetime]] = {}


def get(key: str) -> Any | None:
    entry = _store.get(key)
    if entry is None:
        return None
    value, expiry = entry
    if datetime.now() > expiry:
        del _store[key]
        return None
    return value


def set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    _store[key] = (value, datetime.now() + timedelta(seconds=ttl_seconds))


def bust(*keys: str) -> None:
    for key in keys:
        _store.pop(key, None)


def bust_prefix(prefix: str) -> None:
    for key in list(_store.keys()):
        if key.startswith(prefix):
            del _store[key]

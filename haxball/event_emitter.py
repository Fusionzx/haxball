from __future__ import annotations
import sys
from collections import defaultdict
from inspect import isawaitable
from typing import Any, Callable

Callback = Callable[..., Any]


def normalize_event_name(name: str) -> str:
    """Translates snake_case to camelCase or vice versa, normalizing event names."""
    if not name:
        return ""
    # Convert camelCase to snake_case
    if "_" not in name and any(c.isupper() for c in name):
        s1 = "".join([f"_{c.lower()}" if c.isupper() else c for c in name])
        return s1.lstrip("_")
    # Convert snake_case to camelCase (e.g. on_player_join -> onPlayerJoin)
    if "_" in name:
        parts = name.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])
    return name


class EventEmitter:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callback]] = defaultdict(list)

    def on(self, event: str, callback: Callback) -> Callback:
        normalized = normalize_event_name(event)
        self._handlers[normalized].append(callback)
        return callback

    def off(self, event: str, callback: Callback) -> None:
        normalized = normalize_event_name(event)
        handlers = self._handlers.get(normalized, [])
        self._handlers[normalized] = [h for h in handlers if h is not callback]

    async def emit(self, event: str, *args: Any) -> None:
        normalized = normalize_event_name(event)
        handlers = list(self._handlers.get(normalized, []))
        # Support both snake_case and camelCase listeners
        alt_norm = normalize_event_name(normalized)
        if alt_norm != normalized:
            handlers.extend(self._handlers.get(alt_norm, []))

        for callback in handlers:
            try:
                res = callback(*args)
                if isawaitable(res):
                    await res
            except Exception as e:
                print(
                    f"[event_emitter] Error in handler for '{event}': {e}",
                    file=sys.stderr,
                    flush=True,
                )

    def has_listeners(self, event: str) -> bool:
        normalized = normalize_event_name(event)
        return bool(self._handlers.get(normalized))

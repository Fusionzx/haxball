from __future__ import annotations

from collections import defaultdict
from inspect import isawaitable
from typing import Any, Awaitable, Callable

Callback = Callable[..., Any]


class EventEmitter:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callback]] = defaultdict(list)

    def on(self, event: str, callback: Callback) -> Callback:
        self._handlers[event].append(callback)
        return callback

    def off(self, event: str, callback: Callback) -> None:
        handlers = self._handlers.get(event, [])
        self._handlers[event] = [handler for handler in handlers if handler is not callback]

    async def emit(self, event: str, *args: Any) -> None:
        for callback in list(self._handlers.get(event, [])):
            result = callback(*args)
            if isawaitable(result):
                await result

    def has_listeners(self, event: str) -> bool:
        return bool(self._handlers.get(event))

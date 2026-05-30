from __future__ import annotations
from typing import Any
from ._bridge import ExtendedBrowserBridge

async def native_call(bridge: ExtendedBrowserBridge, method: str, *args: Any) -> Any:
    """Invokes a method directly on the JS RoomObject."""
    return await bridge.call(method, *args)

async def native_call_binary(bridge: ExtendedBrowserBridge, method: str, *args: Any) -> bytes | None:
    """Invokes a method directly on the JS RoomObject and returns bytes."""
    return await bridge.call_binary(method, *args)

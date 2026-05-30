from __future__ import annotations
from typing import Any
from .browser import BrowserBridge


class ExtendedBrowserBridge(BrowserBridge):
    """Extended Browser Bridge that handles additional JS injections if needed,
    and supports capturing binary data like recording playback bytes.
    """

    async def call_binary(self, method: str, *args: Any) -> bytes | None:
        """Calls a room method that returns binary data (like stopRecording)
        and converts it to Python bytes.
        """
        _ALLOWED_BINARY = ["stopRecording"]
        if method not in _ALLOWED_BINARY:
            raise ValueError(f"Method not allowed for binary call: {method}")
        result = await self.page.evaluate(
            """
            async ({ method, args }) => {
              const room = window.__haxpy.room;
              if (!room) throw new Error('Room not initialized');
              const fn = room[method];
              if (typeof fn !== 'function') throw new Error('Unknown room method: ' + method);
              const res = fn.apply(room, args);
              if (res instanceof Uint8Array) {
                  return Array.from(res);
              }
              if (res && typeof res.then === 'function') {
                  const resolved = await res;
                  if (resolved instanceof Uint8Array) {
                      return Array.from(resolved);
                  }
                  return resolved;
              }
              return res;
            }
            """,
            {"method": method, "args": list(args)},
        )
        if isinstance(result, list):
            return bytes(result)
        return result

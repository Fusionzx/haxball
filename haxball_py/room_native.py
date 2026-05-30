from __future__ import annotations
from typing import Any
from .room import Room
from ._native_engine import NativeEngine


class RoomNative(Room):
    """Room class running on the native Node/JS engine backend."""

    def __init__(self, engine: NativeEngine) -> None:
        object.__setattr__(self, "_engine", engine)
        object.__setattr__(self, "_events", None)
        object.__setattr__(self, "_event_handlers", {})
        object.__setattr__(self, "_room_link", None)

    async def call(self, method: str, *args: Any) -> Any:
        return await self._engine.call(method, *args)

    async def get_player(self, player_id: int) -> Any:
        # Override to call engine and deserialize
        result = await self.call("getPlayer", player_id)
        from .models import Player

        return None if result is None else Player.model_validate(result)

    async def get_player_list(self) -> Any:
        result = await self.call("getPlayerList")
        from .models import Player

        return [Player.model_validate(item) for item in result or []]

    async def get_scores(self) -> Any:
        result = await self.call("getScores")
        from .models import Scores

        return None if result is None else Scores.model_validate(result)

    async def get_disc_properties(self, disc_id: int) -> Any:
        result = await self.call("getDiscProperties", disc_id)
        from .models import DiscProperties

        return None if result is None else DiscProperties.from_js(result)

    async def get_player_disc_properties(self, player_id: int) -> Any:
        result = await self.call("getPlayerDiscProperties", player_id)
        from .models import DiscProperties

        return None if result is None else DiscProperties.from_js(result)

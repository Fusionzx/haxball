from __future__ import annotations

from collections.abc import Awaitable, Callable
from inspect import isawaitable
from typing import Any

from .browser import BrowserBridge
from .events import EventEmitter
from .models import DiscProperties, Player, Scores

RoomCallback = Callable[..., Any]


class Room:
    class _EventBinder:
        def __init__(self, room: "Room", name: str) -> None:
            self._room = room
            self._name = name

        def __call__(self, callback: RoomCallback) -> RoomCallback:
            self._room._event_handlers[self._name] = callback
            return callback

        def __repr__(self) -> str:
            return f"<EventBinder {self._name}>"

    _EVENTS = {
        "on_player_join": "onPlayerJoin",
        "on_player_leave": "onPlayerLeave",
        "on_team_victory": "onTeamVictory",
        "on_player_chat": "onPlayerChat",
        "on_player_ball_kick": "onPlayerBallKick",
        "on_team_goal": "onTeamGoal",
        "on_game_start": "onGameStart",
        "on_game_stop": "onGameStop",
        "on_player_admin_change": "onPlayerAdminChange",
        "on_player_team_change": "onPlayerTeamChange",
        "on_player_kicked": "onPlayerKicked",
        "on_game_tick": "onGameTick",
        "on_game_pause": "onGamePause",
        "on_game_unpause": "onGameUnpause",
        "on_positions_reset": "onPositionsReset",
        "on_player_activity": "onPlayerActivity",
        "on_stadium_change": "onStadiumChange",
        "on_room_link": "onRoomLink",
        "on_kick_rate_limit_set": "onKickRateLimitSet",
        "on_teams_lock_change": "onTeamsLockChange",
    }

    def __init__(self, bridge: BrowserBridge) -> None:
        object.__setattr__(self, "_bridge", bridge)
        object.__setattr__(self, "_events", EventEmitter())
        object.__setattr__(self, "_event_handlers", {})
        object.__setattr__(self, "_room_link", None)
        bridge.set_emit_callback(self._handle_js_event)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._EVENTS:
            if value is not None and not callable(value):
                raise TypeError(f"{name} must be callable or None")
            self._event_handlers[name] = value
            return
        object.__setattr__(self, name, value)

    def __getattr__(self, name: str) -> Any:
        if name in self._EVENTS:
            return Room._EventBinder(self, name)
        raise AttributeError(name)

    async def _handle_js_event(self, event_name: str, args: list[Any]) -> None:
        python_name = next((py for py, js in self._EVENTS.items() if js == event_name), None)
        if event_name == "onRoomLink":
            object.__setattr__(self, "_room_link", args[0] if args else None)
        handler = self._event_handlers.get(python_name) if python_name else None
        if handler is None:
            return

        converted = [self._convert_payload(arg) for arg in args]
        result = handler(*converted)
        if isawaitable(result):
            await result

    def _convert_payload(self, value: Any) -> Any:
        if isinstance(value, dict):
            if {"red", "blue", "time"}.issubset(value.keys()):
                return Scores.model_validate(value)
            if {"id", "name", "team"}.issubset(value.keys()):
                return Player.model_validate(value)
            if {"x", "y"}.issubset(value.keys()) and len(value) <= 4:
                from .models import Position
                return Position.model_validate(value)
            if any(key in value for key in ("xspeed", "yspeed", "gravity", "invMass", "bCoef")):
                return DiscProperties.from_js(value)
            return {k: self._convert_payload(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._convert_payload(item) for item in value]
        return value

    @property
    def room_link(self) -> str | None:
        return self._room_link

    async def call(self, method: str, *args: Any) -> Any:
        return await self._bridge.call(method, *args)

    async def send_chat(self, message: str, target_id: int | None = None) -> Any:
        return await self.call("sendChat", message, target_id)

    async def set_player_admin(self, player_id: int, admin: bool) -> Any:
        return await self.call("setPlayerAdmin", player_id, admin)

    async def set_player_team(self, player_id: int, team: int) -> Any:
        return await self.call("setPlayerTeam", player_id, team)

    async def kick_player(self, player_id: int, reason: str = "", ban: bool = False) -> Any:
        return await self.call("kickPlayer", player_id, reason, ban)

    async def clear_ban(self, player_id: int) -> Any:
        return await self.call("clearBan", player_id)

    async def clear_bans(self) -> Any:
        return await self.call("clearBans")

    async def set_score_limit(self, limit: int) -> Any:
        return await self.call("setScoreLimit", limit)

    async def set_time_limit(self, minutes: int) -> Any:
        return await self.call("setTimeLimit", minutes)

    async def set_default_stadium(self, stadium_name: str) -> Any:
        return await self.call("setDefaultStadium", stadium_name)

    async def set_custom_stadium(self, stadium_file_contents: str) -> Any:
        return await self.call("setCustomStadium", stadium_file_contents)

    async def set_teams_lock(self, locked: bool) -> Any:
        return await self.call("setTeamsLock", locked)

    async def set_team_colors(self, team: int, angle: float, text_color: int, colors: list[int]) -> Any:
        return await self.call("setTeamColors", team, angle, text_color, colors)

    async def start_game(self) -> Any:
        return await self.call("startGame")

    async def stop_game(self) -> Any:
        return await self.call("stopGame")

    async def pause_game(self, pause_state: bool) -> Any:
        return await self.call("pauseGame", pause_state)

    async def get_player(self, player_id: int) -> Player | None:
        result = await self.call("getPlayer", player_id)
        return None if result is None else Player.model_validate(result)

    async def get_player_list(self) -> list[Player]:
        result = await self.call("getPlayerList")
        return [Player.model_validate(item) for item in result or []]

    async def get_scores(self) -> Scores | None:
        result = await self.call("getScores")
        return None if result is None else Scores.model_validate(result)

    async def set_password(self, password: str | None) -> Any:
        return await self.call("setPassword", password)

    async def set_require_recaptcha(self, required: bool) -> Any:
        return await self.call("setRequireRecaptcha", required)

    async def reorder_players(self, ids: list[int]) -> Any:
        return await self.call("reorderPlayers", ids)

    async def send_announcement(self, message: str, color: int | None = None, style: str | None = None) -> Any:
        return await self.call("sendAnnouncement", message, color, style)

    async def set_kick_rate_limit(self, min_value: int, rate: int, burst: int, by_player: int | None = None) -> Any:
        return await self.call("setKickRateLimit", min_value, rate, burst, by_player)

    async def set_player_avatar(self, player_id: int, avatar: str | None) -> Any:
        return await self.call("setPlayerAvatar", player_id, avatar)

    async def set_disc_properties(self, disc_id: int, props: dict[str, Any]) -> Any:
        return await self.call("setDiscProperties", disc_id, props)

    async def get_disc_properties(self, disc_id: int) -> DiscProperties | None:
        result = await self.call("getDiscProperties", disc_id)
        return None if result is None else DiscProperties.from_js(result)

    async def set_player_disc_properties(self, player_id: int, props: dict[str, Any]) -> Any:
        return await self.call("setPlayerDiscProperties", player_id, props)

    async def get_player_disc_properties(self, player_id: int) -> DiscProperties | None:
        result = await self.call("getPlayerDiscProperties", player_id)
        return None if result is None else DiscProperties.from_js(result)

    async def get_disc_count(self) -> int:
        return await self.call("getDiscCount")

    async def wait_for_room_link(self, timeout: float | None = None) -> str:
        import asyncio
        loop = asyncio.get_running_loop()
        end = None if timeout is None else loop.time() + timeout
        while True:
            if self._room_link is not None:
                return self._room_link
            if end is not None and loop.time() >= end:
                raise TimeoutError("Timed out waiting for room link")
            await asyncio.sleep(0.05)

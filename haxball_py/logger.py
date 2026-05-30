from __future__ import annotations
from datetime import datetime
from typing import Any

from .player import Player
from .models import Scores


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _pname(p: Any) -> str:
    if isinstance(p, Player):
        return p.name
    if hasattr(p, "name"):
        return p.name
    return str(p)


class RoomLogger:
    """Formats HaxBall room events into human-readable, timestamped log lines.

    The logger is automatically called by :class:`~haxball_py.extended.RoomExtended`
    when ``room.logging`` is ``True`` (the default).  Each event type has its
    own ``_on_<event>`` method; unhandled events are silently ignored.

    Example output::

        14:30:15  Fusion2 has joined
        14:30:20  Fusion2 has left
        14:31:00  Game started
        14:31:05  Fusion2: "hello everyone"
    """

    _SKIP = {"game_tick", "player_activity", "player_ball_kick", "positions_reset", "team_goal"}

    def log_event(self, event: str, *args: Any) -> None:
        """Logs a single room event with a timestamp.

        Dispatches to ``_on_<name>`` where ``name`` is the event name
        with the ``on_`` prefix stripped.

        :param event: The Python-style event name (e.g. ``"on_player_join"``).
        :param args:  The event arguments (players, scores, etc.).
        """
        name = event.removeprefix("on_")
        if name in self._SKIP:
            return
        fmt = getattr(self, f"_on_{name}", None)
        if fmt:
            fmt(*args)
        else:
            self._default(event, *args)

    def _default(self, event: str, *args: Any) -> None:
        print(f"{_ts()}  [{event}] (args: {len(args)})", flush=True)

    def _on_player_join(self, player: Player) -> None:
        print(f"{_ts()}  {player.name} has joined", flush=True)

    def _on_player_leave(self, player: Player) -> None:
        print(f"{_ts()}  {player.name} has left", flush=True)

    def _on_player_chat(self, player: Player, message: str) -> None:
        print(f'{_ts()}  {player.name}: "{message}"', flush=True)

    def _on_player_admin_change(self, changed_player: Player, by_player: Any = None) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        if changed_player.admin:
            print(f"{_ts()}  {changed_player.name} was given admin rights{who}", flush=True)
        else:
            print(f"{_ts()}  {changed_player.name}'s admin rights were taken away{who}", flush=True)

    def _on_player_team_change(self, changed_player: Player, by_player: Any = None) -> None:
        from .enums import Teams

        team_name = (
            Teams(changed_player.team).name
            if hasattr(changed_player, "team")
            else str(changed_player.team)
        )
        who = f" by {_pname(by_player)}" if by_player else ""
        print(f"{_ts()}  {changed_player.name} was moved to {team_name}{who}", flush=True)

    def _on_player_kicked(
        self, kicked_player: Player, reason: str = "", by_player: Any = None
    ) -> None:
        reason_str = f" ({reason})" if reason else ""
        who = f" by {_pname(by_player)}" if by_player else ""
        print(f"{_ts()}  {kicked_player.name} was kicked{reason_str}{who}", flush=True)

    def _on_game_start(self, by_player: Any = None) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        print(f"{_ts()}  Game started{who}", flush=True)

    def _on_game_stop(self, by_player: Any = None) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        print(f"{_ts()}  Game stopped{who}", flush=True)

    def _on_team_victory(self, scores: Scores) -> None:
        from .enums import Teams

        winner = (
            Teams.RED
            if scores.red > scores.blue
            else Teams.BLUE
            if scores.blue > scores.red
            else None
        )
        if winner:
            name = winner.name.capitalize()
            print(f"{_ts()}  {name} team won the match!", flush=True)

    def _on_team_goal(self, team: int) -> None:
        from .enums import Teams

        team_name = Teams(team).name if hasattr(team, "name") else f"Team {team}"
        print(f"{_ts()}  Goal by {team_name}", flush=True)

    def _on_game_pause(self, by_player: Any = None) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        print(f"{_ts()}  Game paused{who}", flush=True)

    def _on_game_unpause(self, by_player: Any = None) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        print(f"{_ts()}  Game unpaused{who}", flush=True)

    def _on_stadium_change(self, stadium_name: str, by_player: Any = None) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        print(f"{_ts()}  Stadium changed to {stadium_name}{who}", flush=True)

    def _on_room_link(self, link: str) -> None:
        print(f"{_ts()}  Room link: {link}", flush=True)

    def _on_kick_rate_limit_set(
        self, min_value: int, rate: int, burst: int, by_player: Any = None
    ) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        print(
            f"{_ts()}  Kick rate limit set to (min: {min_value}, rate: {rate}, burst: {burst}){who}",
            flush=True,
        )

    def _on_teams_lock_change(self, locked: bool, by_player: Any = None) -> None:
        who = f" by {_pname(by_player)}" if by_player else ""
        state = "locked" if locked else "unlocked"
        print(f"{_ts()}  Teams {state}{who}", flush=True)

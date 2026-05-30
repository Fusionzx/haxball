from __future__ import annotations
import collections.abc
from typing import Any, Callable, Iterator
from .player import Player
from .enums import Teams

class PlayerList(collections.abc.MutableMapping):
    def __init__(self, players: dict[int, Player] | None = None) -> None:
        self._players: dict[int, Player] = players if players is not None else {}

    @property
    def size(self) -> int:
        """Returns the number of players in the list."""
        return len(self._players)

    def __getitem__(self, key: int) -> Player:
        return self._players[key]

    def __setitem__(self, key: int, value: Player) -> None:
        self._players[key] = value

    def __delitem__(self, key: int) -> None:
        del self._players[key]

    def __iter__(self) -> Iterator[int]:
        return iter(self._players)

    def __len__(self) -> int:
        return len(self._players)

    def add(self, player: Player) -> None:
        """Adds a player to the list."""
        self._players[player.id] = player

    def remove(self, player: Player | int) -> None:
        """Removes a player from the list."""
        pid = player.id if isinstance(player, Player) else player
        if pid in self._players:
            del self._players[pid]

    def get(self, predicate: int | Callable[[Player], bool]) -> Player | None:
        """Gets a player by ID or by a predicate function."""
        if isinstance(predicate, int):
            return self._players.get(predicate)
        for p in self._players.values():
            if predicate(p):
                return p
        return None

    def get_all(self, predicate: Callable[[Player], bool]) -> PlayerList:
        """Gets all players matching a predicate function."""
        matched = {p.id: p for p in self._players.values() if predicate(p)}
        return PlayerList(matched)

    def values(self) -> list[Player]:
        """Returns a list of all Player objects."""
        return list(self._players.values())

    def order(self, room: Any) -> PlayerList:
        """Returns a new PlayerList ordered or sorted by something standard (e.g., ID or custom order)."""
        # HaxBall reorder/order normally retains order of IDs
        sorted_players = sorted(self._players.values(), key=lambda p: p.id)
        return PlayerList({p.id: p for p in sorted_players})

    def first(self) -> Player | None:
        """Returns the first player in the list, or None."""
        if not self._players:
            return None
        return next(iter(self._players.values()))

    def last(self) -> Player | None:
        """Returns the last player in the list, or None."""
        if not self._players:
            return None
        return list(self._players.values())[-1]

    def get_by_name(self, name: str) -> PlayerList:
        """Filters players by name."""
        return self.get_all(lambda p: p.name == name)

    def get_by_auth(self, auth: str) -> Player | None:
        """Gets a player by auth key."""
        return self.get(lambda p: p.auth == auth)

    def get_by_conn_or_ip(self, conn_or_ip: str) -> PlayerList:
        """Filters players by connection string or IP address."""
        return self.get_all(lambda p: p.conn == conn_or_ip or p.ip == conn_or_ip)

    def kick(self, reason: str = "") -> None:
        """Kicks all players in this list."""
        for p in list(self._players.values()):
            p.kick(reason)

    def ban(self, reason: str = "") -> None:
        """Bans all players in this list."""
        for p in list(self._players.values()):
            p.ban(reason)

    def spectators(self) -> PlayerList:
        """Filters spectators."""
        return self.get_all(lambda p: p.team == Teams.SPECTATORS)

    def red(self) -> PlayerList:
        """Filters red team players."""
        return self.get_all(lambda p: p.team == Teams.RED)

    def blue(self) -> PlayerList:
        """Filters blue team players."""
        return self.get_all(lambda p: p.team == Teams.BLUE)

    def teams(self) -> PlayerList:
        """Filters players on red or blue team."""
        return self.get_all(lambda p: p.team in (Teams.RED, Teams.BLUE))

    def admins(self) -> PlayerList:
        """Filters admins."""
        return self.get_all(lambda p: p.admin)

    def reply(self, message: str, color: int | None = None, style: str | None = None) -> None:
        """Replies to all players in the list."""
        for p in self._players.values():
            p.reply(message, color, style)

    def __str__(self) -> str:
        names = ", ".join(p.name for p in self._players.values())
        return f"PlayerList(size={self.size}, [{names}])"

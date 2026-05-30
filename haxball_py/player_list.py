from __future__ import annotations
import collections.abc
from typing import Any, Callable, Iterator
from .player import Player
from .enums import Teams


class PlayerList(collections.abc.MutableMapping):
    """A mapping of player IDs to :class:`~haxball_py.player.Player` objects.

    Behaves like a dict::

        player = room.players[1]       # get by ID
        for pid, p in room.players.items(): ...

    It also provides chainable filter methods (e.g. ``.admins().red()``)
    and bulk operations (``.kick()``, ``.reply()``, etc.).
    """

    def __init__(self, players: dict[int, Player] | None = None) -> None:
        self._players: dict[int, Player] = players if players is not None else {}

    @property
    def size(self) -> int:
        """The number of players currently in the list."""
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
        """Adds a player to the list.

        :param player: The :class:`~haxball_py.player.Player` to add.
        """
        self._players[player.id] = player

    def remove(self, player: Player | int) -> None:
        """Removes a player from the list.

        :param player: A :class:`~haxball_py.player.Player` instance or a numeric ID.
        """
        pid = player.id if isinstance(player, Player) else player
        if pid in self._players:
            del self._players[pid]

    def get(self, predicate: int | Callable[[Player], bool]) -> Player | None:
        """Finds a single player by ID or a predicate function.

        :param predicate: A player ID, or a callable ``(Player) -> bool``.
        :returns: The first matching player, or ``None``.
        """
        if isinstance(predicate, int):
            return self._players.get(predicate)
        for p in self._players.values():
            if predicate(p):
                return p
        return None

    def get_all(self, predicate: Callable[[Player], bool]) -> PlayerList:
        """Finds all players matching a predicate.

        :param predicate: A callable ``(Player) -> bool``.
        :returns: A new :class:`PlayerList` with the matches.
        """
        matched = {p.id: p for p in self._players.values() if predicate(p)}
        return PlayerList(matched)

    def values(self) -> list[Player]:
        """Returns all players as a plain list."""
        return list(self._players.values())

    def order(self, room: Any) -> PlayerList:
        """Returns a new :class:`PlayerList` sorted by player ID."""
        sorted_players = sorted(self._players.values(), key=lambda p: p.id)
        return PlayerList({p.id: p for p in sorted_players})

    def first(self) -> Player | None:
        """The first player in the list (insertion order), or ``None``."""
        if not self._players:
            return None
        return next(iter(self._players.values()))

    def last(self) -> Player | None:
        """The last player in the list, or ``None``."""
        if not self._players:
            return None
        return list(self._players.values())[-1]

    def get_by_name(self, name: str) -> PlayerList:
        """Filters players whose name exactly matches the given string."""
        return self.get_all(lambda p: p.name == name)

    def get_by_auth(self, auth: str) -> Player | None:
        """Finds a player by their public auth token.

        :param auth: The auth string to match.
        :returns: The matching :class:`~haxball_py.player.Player`, or ``None``.
        """
        return self.get(lambda p: p.auth == auth)

    def get_by_conn_or_ip(self, conn_or_ip: str) -> PlayerList:
        """Filters players by connection fingerprint or IP address.

        :param conn_or_ip: A ``conn`` string or an IP address.
        """
        return self.get_all(lambda p: p.conn == conn_or_ip or p.ip == conn_or_ip)

    def kick(self, reason: str = "") -> None:
        """Kicks every player in this list.

        :param reason: An optional reason shown to each kicked player.
        """
        for p in list(self._players.values()):
            p.kick(reason)

    def ban(self, reason: str = "") -> None:
        """Bans every player in this list.

        :param reason: An optional reason shown to each banned player.
        """
        for p in list(self._players.values()):
            p.ban(reason)

    def spectators(self) -> PlayerList:
        """Filters players who are spectating."""
        return self.get_all(lambda p: p.team == Teams.SPECTATORS)

    def red(self) -> PlayerList:
        """Filters players on the red team."""
        return self.get_all(lambda p: p.team == Teams.RED)

    def blue(self) -> PlayerList:
        """Filters players on the blue team."""
        return self.get_all(lambda p: p.team == Teams.BLUE)

    def teams(self) -> PlayerList:
        """Filters players on either the red or blue team (excludes spectators)."""
        return self.get_all(lambda p: p.team in (Teams.RED, Teams.BLUE))

    def admins(self) -> PlayerList:
        """Filters players who have admin rights."""
        return self.get_all(lambda p: p.admin)

    def reply(self, message: str, color: int | None = None, style: str | None = None) -> None:
        """Sends a private message to every player in this list.

        :param message: The message text.
        :param color:  An RGB integer color.
        :param style:  One of ``"normal"``, ``"bold"``, ``"italic"``, etc.
        """
        for p in self._players.values():
            p.reply(message, color, style)

    def __str__(self) -> str:
        names = ", ".join(p.name for p in self._players.values())
        return f"PlayerList(size={self.size}, [{names}])"

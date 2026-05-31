from __future__ import annotations
import asyncio
import weakref
from typing import Any, TYPE_CHECKING
from .disc import AbstractDisc
from .utils import decode_ip_from_conn

if TYPE_CHECKING:
    from .extended import RoomExtended
    from .models import Position


class Player(AbstractDisc):
    """Represents a player in the HaxBall room.

    A Player is also a :class:`~haxball.disc.Disc` (via :class:`AbstractDisc`),
    so all disc properties (``x``, ``y``, ``radius``, ``xspeed``, etc.) are
    available and any write to them automatically syncs back to the game engine.

    Typical usage::

        player.admin = True                     # give admin rights
        player.team = Teams.Red                 # move to red team
        player.kick("No reason")                # kick from room
        player.reply("Hello!", color=0x00FF00)  # private message
        print(player.name, player.ip)           # read-only metadata
    """

    __slots__ = (
        "_id",
        "_name",
        "_auth",
        "_conn",
        "_ip",
        "_admin",
        "_team",
        "_position",
        "_roles",
        "_room_ref",
    )

    def __init__(self, id: int, name: str, team: int, **kwargs: Any) -> None:
        kwargs.setdefault("is_player", True)
        kwargs.setdefault("disc_id", id)
        super().__init__(**kwargs)
        self._id = id
        self._name = name
        self._team = team
        self._admin: bool = kwargs.get("admin", False)
        self._auth: str | None = kwargs.get("auth")
        self._conn: str | None = kwargs.get("conn")
        self._ip: str | None = decode_ip_from_conn(self._conn)
        self._position: Position | None = kwargs.get("position")
        self._roles: list[Any] = kwargs.get("roles") if kwargs.get("roles") is not None else []

        room = kwargs.get("room")
        self._room_ref = weakref.ref(room) if room is not None else None
        if room is not None:
            self._room = room

    @property
    def room(self) -> RoomExtended | None:
        """The :class:`RoomExtended` this player belongs to, or ``None``."""
        if self._room_ref is not None:
            return self._room_ref()
        return None

    @property
    def id(self) -> int:
        """The player's unique numeric identifier.

        IDs are assigned on join and never change during the session.
        When a player leaves and rejoins they get a **new** ID.
        """
        return self._id

    @property
    def name(self) -> str:
        """The player's display name as shown in-game."""
        return self._name

    @property
    def auth(self) -> str | None:
        """The player's public authentication token.

        This is a persistent identifier that can be used to recognise
        the same player across sessions.  ``None`` if validation failed.
        """
        return self._auth

    @property
    def conn(self) -> str | None:
        """A connection fingerprint unique to the player's network.

        Two players behind the same public IP share the same ``conn`` value.
        Use :attr:`ip` for the decoded IP address.
        """
        return self._conn

    @property
    def ip(self) -> str | None:
        """The player's IP address, decoded from the connection string.

        This is derived from ``conn`` and is ``None`` if ``conn`` is empty.
        """
        return self._ip

    @property
    def team(self) -> int:
        """The team the player is currently on.

        Possible values are defined in :class:`~haxball.enums.Teams`:

        * ``Teams.Spectators`` (0)
        * ``Teams.Red`` (1)
        * ``Teams.Blue`` (2)

        Setting this property moves the player in-game immediately::

            player.team = Teams.Red
        """
        return self._team

    @team.setter
    def team(self, value: int) -> None:
        self._team = value
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_team(self._id, value))

    @property
    def admin(self) -> bool:
        """Whether the player has admin rights.

        Setting to ``True`` / ``False`` immediately reflects in-game::

            player.admin = True           # give admin
            player.admin = False          # remove admin
        """
        return self._admin

    @admin.setter
    def admin(self, value: bool) -> None:
        self._admin = value
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_admin(self._id, value))

    @property
    def position(self) -> Position | None:
        """The player's current ``(x, y)`` position on the field.

        This is a :class:`~haxball.models.Position` named tuple, or
        ``None`` when the player is spectating or no game is running.
        Setting this value also updates the player's disc position.
        """
        return self._position

    @position.setter
    def position(self, pos: Position | None) -> None:
        self._position = pos
        if pos is not None:
            self.x = pos.x
            self.y = pos.y

    @property
    def roles(self) -> list[Any]:
        """Custom permission roles attached to this player.

        Roles are checked by :meth:`Command.is_allowed
        <haxball.command.Command.is_allowed>` to decide whether
        a player can run a given command.

        The ``"admin"`` role is automatically managed — it is added when
        :attr:`admin` becomes ``True`` and removed when it becomes ``False``.
        """
        return self._roles

    def kick(self, reason: str = "") -> None:
        """Kicks the player from the room.

        :param reason: Optional message shown to the kicked player.
        """
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.kick_player(self._id, reason, False))

    def ban(self, reason: str = "") -> None:
        """Kicks **and bans** the player from the room.

        The ban is IP-based — the player will not be able to rejoin
        until the ban is cleared via :meth:`RoomExtended.unban` or
        :meth:`RoomExtended.unban_all`.

        :param reason: Optional message shown to the banned player.
        """
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.kick_player(self._id, reason, True))

    def reply(
        self,
        message: str,
        color: int | None = None,
        style: str | None = None,
        sound: int | None = None,
    ) -> None:
        """Sends a private message visible only to this player.

        This is equivalent to ``await room.send(message, target_id=self.id)``.

        :param message: The message text.
        :param color:  An RGB integer (e.g. ``0x00FF00`` for green).
        :param style:  One of ``"normal"``, ``"bold"``, ``"italic"``,
                       ``"small"``, ``"small-bold"``, ``"small-italic"``.
        :param sound:  Sound effect (0 = none, 1 = normal, 2 = notification).
        """
        room = self.room
        if room is not None:
            asyncio.create_task(
                room.send(message, color=color, style=style, sound=sound, target_id=self._id)
            )

    def set_avatar(self, avatar: str) -> None:
        """Overrides the player's avatar with a custom image URL.

        :param avatar: A URL pointing to an image.
        """
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_avatar(self._id, avatar))

    def clear_avatar(self) -> None:
        """Removes any custom avatar override, restoring the default."""
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_avatar(self._id, None))

    def add_role(self, role: Any) -> None:
        """Adds a permission role to the player.

        :param role: Any hashable value (typically a string like ``"mod"``).
        """
        if role not in self._roles:
            self._roles.append(role)

    def remove_role(self, role: Any) -> None:
        """Removes a previously added permission role.

        :param role: The role to remove (no-op if absent).
        """
        if role in self._roles:
            self._roles.remove(role)

    def has_role(self, role: Any) -> bool:
        """Checks whether the player has a specific role.

        :param role: The role to check.
        :returns: ``True`` if the role is present.
        """
        return role in self._roles

    def tag(self) -> str:
        """Returns a human-readable ``"Name #id"`` string."""
        return f"{self._name} #{self._id}"

    def mention(self) -> str:
        """Returns an ``@Name`` mention string."""
        return f"@{self._name}"

    def can_kick(self, disc: AbstractDisc) -> bool:
        """Checks whether the player is within kicking distance of a disc.

        The player's radius is assumed to be 15 and the target disc's
        radius 10 when the respective properties are ``None``.

        :param disc: The target disc (player, ball, etc.).
        :returns: ``True`` if the player can kick the disc.
        """
        if self.x is None or self.y is None or disc.x is None or disc.y is None:
            return False
        dist = self.distance_to(disc)
        if dist is None:
            return False
        r1 = self.radius if self.radius is not None else 15.0
        r2 = disc.radius if disc.radius is not None else 10.0
        return dist <= (r1 + r2 + 4.0)

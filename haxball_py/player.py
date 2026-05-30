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
    __slots__ = (
        "_id", "_name", "_auth", "_conn", "_ip",
        "_admin", "_team", "_position", "_roles", "_room_ref"
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
        if self._room_ref is not None:
            return self._room_ref()
        return None

    @property
    def id(self) -> int: return self._id

    @property
    def name(self) -> str: return self._name

    @property
    def auth(self) -> str | None: return self._auth

    @property
    def conn(self) -> str | None: return self._conn

    @property
    def ip(self) -> str | None: return self._ip

    @property
    def team(self) -> int:
        room = self.room
        if room is not None:
            return self._team
        return self._team
    @team.setter
    def team(self, value: int) -> None:
        self._team = value
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_team(self._id, value))

    @property
    def admin(self) -> bool:
        return self._admin
    @admin.setter
    def admin(self, value: bool) -> None:
        self._admin = value
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_admin(self._id, value))

    @property
    def position(self) -> Position | None:
        return self._position
    @position.setter
    def position(self, pos: Position | None) -> None:
        self._position = pos
        if pos is not None:
            self.x = pos.x
            self.y = pos.y

    @property
    def roles(self) -> list[Any]:
        return self._roles

    def kick(self, reason: str = "") -> None:
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.kick_player(self._id, reason, False))

    def ban(self, reason: str = "") -> None:
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.kick_player(self._id, reason, True))

    def reply(self, message: str, color: int | None = None, style: str | None = None) -> None:
        room = self.room
        if room is not None:
            room.send(message, color=color, style=style, target_id=self._id)

    def set_avatar(self, avatar: str) -> None:
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_avatar(self._id, avatar))

    def clear_avatar(self) -> None:
        room = self.room
        if room is not None:
            asyncio.create_task(room.native.set_player_avatar(self._id, None))

    def add_role(self, role: Any) -> None:
        if role not in self._roles:
            self._roles.append(role)

    def remove_role(self, role: Any) -> None:
        if role in self._roles:
            self._roles.remove(role)

    def has_role(self, role: Any) -> bool:
        return role in self._roles

    def tag(self) -> str:
        return f"{self._name} #{self._id}"

    def mention(self) -> str:
        return f"@{self._name}"

    def can_kick(self, disc: AbstractDisc) -> bool:
        if self.x is None or self.y is None or disc.x is None or disc.y is None:
            return False
        dist = self.distance_to(disc)
        if dist is None:
            return False
        r1 = self.radius if self.radius is not None else 15.0
        r2 = disc.radius if disc.radius is not None else 10.0
        return dist <= (r1 + r2 + 4.0)

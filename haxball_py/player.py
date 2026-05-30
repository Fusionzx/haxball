from __future__ import annotations
import weakref
from typing import Any, TYPE_CHECKING
from .disc import AbstractDisc
from .utils import decode_ip_from_conn

if TYPE_CHECKING:
    from .extended import RoomExtended
    from .models import Position

class Player(AbstractDisc):
    __slots__ = (
        "id", "name", "auth", "conn", "ip", "admin", "team",
        "position", "roles", "_room_ref"
    )

    def __init__(self, id: int, name: str, team: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.id = id
        self.name = name
        self.team = team
        self.admin: bool = kwargs.get("admin", False)
        self.auth: str | None = kwargs.get("auth")
        self.conn: str | None = kwargs.get("conn")
        self.ip: str | None = decode_ip_from_conn(self.conn)
        self.position: Position | None = kwargs.get("position")
        self.roles: list[Any] = kwargs.get("roles") if kwargs.get("roles") is not None else []
        
        room = kwargs.get("room")
        self._room_ref = weakref.ref(room) if room is not None else None

    @property
    def room(self) -> RoomExtended | None:
        if self._room_ref is not None:
            return self._room_ref()
        return None

    def kick(self, reason: str = "") -> None:
        """Kicks the player from the room."""
        room = self.room
        if room is not None:
            room.native.kick_player(self.id, reason, False)

    def ban(self, reason: str = "") -> None:
        """Bans the player from the room."""
        room = self.room
        if room is not None:
            room.native.kick_player(self.id, reason, True)

    def reply(self, message: str, color: int | None = None, style: str | None = None) -> None:
        """Sends a private message to this player."""
        room = self.room
        if room is not None:
            room.send(message, color=color, style=style, target_id=self.id)

    def set_avatar(self, avatar: str) -> None:
        """Sets the player avatar."""
        room = self.room
        if room is not None:
            room.native.set_player_avatar(self.id, avatar)

    def clear_avatar(self) -> None:
        """Clears the player avatar."""
        room = self.room
        if room is not None:
            room.native.set_player_avatar(self.id, None)

    def add_role(self, role: Any) -> None:
        """Adds a role to the player."""
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: Any) -> None:
        """Removes a role from the player."""
        if role in self.roles:
            self.roles.remove(role)

    def has_role(self, role: Any) -> bool:
        """Checks if the player has the specified role."""
        return role in self.roles

    def tag(self) -> str:
        """Returns the player's tag in the format Name#ID."""
        return f"{self.name} #{self.id}"

    def mention(self) -> str:
        """Returns the player's mention string."""
        return f"@{self.name}"

    def can_kick(self, disc: AbstractDisc) -> bool:
        """Returns True if the player is close enough to kick the specified disc."""
        if self.x is None or self.y is None or disc.x is None or disc.y is None:
            return False
        dist = self.distance_to(disc)
        if dist is None:
            return False
        r1 = self.radius if self.radius is not None else 15.0
        r2 = disc.radius if disc.radius is not None else 10.0
        return dist <= (r1 + r2 + 4.0)

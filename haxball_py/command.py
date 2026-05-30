from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import Player
    from .extended import RoomExtended

NUMBER_RE = re.compile(r"^\d+$")
YESNO_RE = re.compile(r"^(y(es)?|n(o)?)$", re.IGNORECASE)
EXTENDED_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")

@dataclass(slots=True)
class CommandArgument:
    raw: str
    number: bool = False
    yesno: bool = False
    password: bool = False
    extended: bool = False
    special_extended: bool = False

    def __post_init__(self) -> None:
        self.number = bool(NUMBER_RE.match(self.raw))
        self.yesno = bool(YESNO_RE.match(self.raw))
        # Default password checks if length is reasonably strong or has values
        self.password = len(self.raw) >= 4
        self.extended = bool(EXTENDED_RE.match(self.raw))
        self.special_extended = len(self.raw) > 0

    def to_number(self) -> int:
        try:
            return int(self.raw)
        except ValueError:
            return 0

    def to_string(self) -> str:
        return self.raw


@dataclass(slots=True)
class CommandExecInfo:
    player: Player
    message: str
    room: RoomExtended
    at: datetime
    arguments: list[CommandArgument]


@dataclass(slots=True)
class Command:
    name: str
    func: Callable[[CommandExecInfo], Awaitable[None] | None]
    aliases: list[str] = field(default_factory=list)
    roles: list[Any] = field(default_factory=list)
    desc: str = ""
    usage: str = ""
    delete_message: bool = True

    def is_allowed(self, player: Player) -> bool:
        """Checks if the player is allowed to execute this command based on roles."""
        if not self.roles:
            return True
        for role in self.roles:
            # Check if role matches a role in player roles or player's admin status
            if role == "admin" and player.admin:
                return True
            if player.has_role(role):
                return True
        return False

    async def run(self, info: CommandExecInfo) -> None:
        """Executes the command function."""
        import inspect
        res = self.func(info)
        if inspect.isawaitable(res):
            await res

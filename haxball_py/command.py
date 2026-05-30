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
    """A single parsed argument from a chat command.

    Provides convenient type-checks and conversion helpers.
    Access individual arguments via ``info.arguments[i]`` in a command handler.
    """

    raw: str
    number: bool = False
    yesno: bool = False
    password: bool = False
    extended: bool = False
    special_extended: bool = False

    def __post_init__(self) -> None:
        self.number = bool(NUMBER_RE.match(self.raw))
        self.yesno = bool(YESNO_RE.match(self.raw))
        self.password = len(self.raw) >= 4
        self.extended = bool(EXTENDED_RE.match(self.raw))
        self.special_extended = len(self.raw) > 0

    def to_number(self) -> int:
        """Parses the argument as an integer.

        :returns: The integer value, or ``0`` if it cannot be parsed.
        """
        try:
            return int(self.raw)
        except ValueError:
            return 0

    def to_string(self) -> str:
        """Returns the raw argument string."""
        return self.raw


@dataclass(slots=True)
class CommandExecInfo:
    """Information passed to a command's execution function.

    Attributes:
        player:   The :class:`~haxball_py.player.Player` who ran the command.
        message:  The raw chat message (including prefix).
        room:     The :class:`~haxball_py.extended.RoomExtended` instance.
        at:       The :class:`~datetime.datetime` when the command was executed.
        arguments: List of :class:`CommandArgument` parsed from the message.
    """

    player: Player
    message: str
    room: RoomExtended
    at: datetime
    arguments: list[CommandArgument]


@dataclass(slots=True)
class Command:
    """A chat command registered on the room.

    Use :meth:`RoomExtended.command <haxball_py.extended.RoomExtended.command>`
    or the :func:`@module_command <haxball_py.module.module_command>` decorator
    to add commands.
    """

    name: str
    func: Callable[[CommandExecInfo], Awaitable[None] | None]
    aliases: list[str] = field(default_factory=list)
    roles: list[Any] = field(default_factory=list)
    desc: str = ""
    usage: str = ""
    delete_message: bool = True

    def is_allowed(self, player: Player) -> bool:
        """Checks if the player is allowed to execute this command.

        A command is allowed if:

        * The command has no role restrictions (``roles`` is empty), **or**
        * The player has the ``"admin"`` role and is an admin, **or**
        * The player has **all** required roles.

        :param player: The player to check.
        :returns: ``True`` if the player can run the command.
        """
        if not self.roles:
            return True
        for role in self.roles:
            if role == "admin" and player.admin:
                return True
            if player.has_role(role):
                return True
        return False

    async def run(self, info: CommandExecInfo) -> None:
        """Executes the command function with the given info.

        :param info: The :class:`CommandExecInfo` object.
        """
        import inspect

        res = self.func(info)
        if inspect.isawaitable(res):
            await res

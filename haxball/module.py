from __future__ import annotations
from typing import Any, Callable, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .extended import RoomExtended

# Standard translator stub
TranslatorFunc = Callable[[str, dict[str, Any] | None], str]


def default_translator(key: str, params: dict[str, Any] | None = None) -> str:
    if params:
        try:
            return key.format(**params)
        except Exception:
            pass
    return key


class ModuleMeta(type):
    """Metaclass that scans a module class for decorated command/event methods.

    At class creation time it collects:

    * Methods decorated with :func:`module_command` → stored in ``_commands``
    * Methods decorated with :func:`event`           → stored in ``_events``
    * Methods decorated with :func:`custom_event`    → stored in ``_custom_events``
    """

    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        cls = super().__new__(mcs, name, bases, attrs)
        cls._commands = []
        cls._events = []
        cls._custom_events = []

        for key, value in attrs.items():
            if hasattr(value, "_is_module_command"):
                cls._commands.append((key, getattr(value, "_command_options")))
            if hasattr(value, "_is_event"):
                cls._events.append((key, value.__name__))
            if hasattr(value, "_is_custom_event"):
                cls._custom_events.append((key, value.__name__))
        return cls


class Module(metaclass=ModuleMeta):
    """Base class for creating modular room logic.

    Extend this class and use the decorators :func:`@event`,
    :func:`@module_command` and :func:`@custom_event` to declare event handlers
    and chat commands.  Register the module via
    :meth:`RoomExtended.module() <haxball.extended.RoomExtended.module>`.

    Usage::

        @module
        class MyModule(Module):
            @event
            async def on_player_join(self, player: Player):
                player.reply("Welcome!")

            @module_command(name="ping", desc="Replies with pong")
            async def ping(self, info: CommandExecInfo):
                info.player.reply("pong!")
    """

    _commands: list[tuple[str, dict[str, Any]]] = []
    _events: list[tuple[str, str]] = []
    _custom_events: list[tuple[str, str]] = []

    def __init__(self, room: RoomExtended, settings: dict[str, Any] | None = None) -> None:
        self.room = room
        self.settings: dict[str, Any] = settings if settings is not None else {}
        self.translate: TranslatorFunc = default_translator


def module(cls: Type[Module]) -> Type[Module]:
    """Class decorator that marks a :class:`Module` subclass for registration.

    Usage::

        @module
        class MyModule(Module):
            ...
    """
    return cls


def module_command(
    name: str | None = None,
    aliases: list[str] | None = None,
    roles: list[Any] | None = None,
    desc: str = "",
    usage: str = "",
    delete_message: bool = True,
) -> Callable:
    """Decorator that registers a method as a chat command.

    :param name: The command name. Defaults to the method name.
    :param aliases: Alternative names that trigger this command.
    :param roles: Required roles (e.g. ``["admin"]``). Empty means anyone.
    :param desc: Human-readable description (used by help commands).
    :param usage: Usage string (e.g. ``"kick #id reason"``).
    :param delete_message: Whether to remove the player's chat message.

    Usage::

        @module_command(name="kick", roles=["admin"])
        async def kick(self, info: CommandExecInfo):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        fn._is_module_command = True
        fn._command_options = {
            "name": name or fn.__name__,
            "aliases": aliases or [],
            "roles": roles or [],
            "desc": desc,
            "usage": usage,
            "delete_message": delete_message,
        }
        return fn

    return decorator


def event(fn: Callable) -> Callable:
    """Decorator that registers a method as a room event handler.

    The method name must match the event (e.g. ``on_player_join``).

    The handler is called **after** the built-in logger and **before**
    any handler set directly on ``room.native``.

    Usage::

        @event
        async def on_player_join(self, player: Player):
            player.reply("Welcome!")
    """
    fn._is_event = True
    return fn


def custom_event(fn: Callable) -> Callable:
    """Decorator that registers a method as a custom event handler.

    Custom events are emitted via ``room.custom_events.emit("event_name", ...)``.

    Usage::

        @custom_event
        async def on_player_afk(self, player: Player):
            print(f"{player.name} is now AFK")
    """
    fn._is_custom_event = True
    return fn

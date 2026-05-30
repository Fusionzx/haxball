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
    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        cls = super().__new__(mcs, name, bases, attrs)
        cls._commands = []
        cls._events = []
        cls._custom_events = []
        
        # Scan attributes for decorated methods
        for key, value in attrs.items():
            if hasattr(value, "_is_module_command"):
                cls._commands.append((key, getattr(value, "_command_options")))
            if hasattr(value, "_is_event"):
                cls._events.append((key, value.__name__))
            if hasattr(value, "_is_custom_event"):
                cls._custom_events.append((key, value.__name__))
        return cls


class Module(metaclass=ModuleMeta):
    _commands: list[tuple[str, dict[str, Any]]] = []
    _events: list[tuple[str, str]] = []
    _custom_events: list[tuple[str, str]] = []

    def __init__(self, room: RoomExtended, settings: dict[str, Any] | None = None) -> None:
        self.room = room
        self.settings: dict[str, Any] = settings if settings is not None else {}
        self.translate: TranslatorFunc = default_translator


def module(cls: Type[Module]) -> Type[Module]:
    """Decorator to mark a class as a Room Module."""
    return cls


def module_command(
    name: str | None = None,
    aliases: list[str] | None = None,
    roles: list[Any] | None = None,
    desc: str = "",
    usage: str = "",
    delete_message: bool = True
) -> Callable:
    """Decorator to define a command inside a Module."""
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
    """Decorator to define a room event handler inside a Module."""
    fn._is_event = True
    return fn


def custom_event(fn: Callable) -> Callable:
    """Decorator to define a custom event handler inside a Module."""
    fn._is_custom_event = True
    return fn

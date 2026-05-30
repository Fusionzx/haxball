from .client import HaxballClient
from .config import GeoConfig, HaxballConfig
from .events import EventEmitter
from .models import (
    DiscProperties,
    Player as NativePlayer,
    Position,
    Scores,
)

# Extended imports
from .extended import RoomExtended, HaxballClientExtended
from .player import Player
from .player_list import PlayerList
from .disc import AbstractDisc, Disc
from .command import Command, CommandExecInfo, CommandArgument
from .module import Module, module, module_command, event, custom_event
from .enums import Teams, ChatStyle, ChatSounds, Stadiums, Colors
from ._hbinit import HaxballJS

__all__ = [
    "DiscProperties",
    "EventEmitter",
    "GeoConfig",
    "HaxballClient",
    "HaxballConfig",
    "NativePlayer",
    "Position",
    "Scores",
    
    # Extended exports
    "RoomExtended",
    "HaxballClientExtended",
    "Player",
    "PlayerList",
    "AbstractDisc",
    "Disc",
    "Command",
    "CommandExecInfo",
    "CommandArgument",
    "Module",
    "module",
    "module_command",
    "event",
    "custom_event",
    "Teams",
    "ChatStyle",
    "ChatSounds",
    "Stadiums",
    "Colors",
    "HaxballJS",
]


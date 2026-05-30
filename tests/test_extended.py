import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from haxball_py import (
    Player,
    PlayerList,
    Command,
    CommandArgument,
    CommandExecInfo,
    Module,
    module,
    module_command,
    event,
    Teams
)

def test_command_argument_parsing():
    arg_num = CommandArgument("123")
    assert arg_num.number is True
    assert arg_num.to_number() == 123
    assert arg_num.to_string() == "123"

    arg_str = CommandArgument("hello")
    assert arg_str.number is False
    assert arg_str.yesno is False
    assert arg_str.to_number() == 0

    arg_yes = CommandArgument("yes")
    assert arg_yes.yesno is True


def test_player_list_filters():
    room_mock = MagicMock()
    p1 = Player(id=1, name="Alice", team=Teams.RED, admin=True, room=room_mock)
    p2 = Player(id=2, name="Bob", team=Teams.BLUE, admin=False, room=room_mock)
    p3 = Player(id=3, name="Charlie", team=Teams.SPECTATORS, admin=False, room=room_mock)

    plist = PlayerList()
    plist.add(p1)
    plist.add(p2)
    plist.add(p3)

    assert plist.size == 3
    assert len(plist.red()) == 1
    assert plist.red().first().name == "Alice"
    assert len(plist.blue()) == 1
    assert len(plist.spectators()) == 1
    assert len(plist.admins()) == 1
    assert plist.get_by_name("Bob").first().id == 2


@pytest.mark.asyncio
async def test_command_execution():
    room_mock = MagicMock()
    player = Player(id=1, name="Alice", team=1, admin=True, room=room_mock)
    
    called = False
    async def dummy_cmd(info: CommandExecInfo):
        nonlocal called
        called = True
        assert info.player.name == "Alice"
        assert len(info.arguments) == 1
        assert info.arguments[0].raw == "test"

    cmd = Command(
        name="test",
        func=dummy_cmd,
        roles=["admin"]
    )

    assert cmd.is_allowed(player) is True
    
    info = CommandExecInfo(
        player=player,
        message="!test test",
        room=room_mock,
        at=datetime.now(),
        arguments=[CommandArgument("test")]
    )
    
    await cmd.run(info)
    assert called is True


@pytest.mark.asyncio
async def test_module_registration():
    room_mock = MagicMock()
    room_mock.commands = []
    room_mock.modules = {}
    room_mock.custom_events = MagicMock()

    @module
    class MyTestModule(Module):
        @module_command(name="ping")
        async def ping_cmd(self, info: CommandExecInfo):
            pass

        @event
        async def on_player_join(self, player: Player):
            pass

    # We can manually register or verify metadata discovery
    assert len(MyTestModule._commands) == 1
    assert MyTestModule._commands[0][0] == "ping_cmd"
    assert MyTestModule._commands[0][1]["name"] == "ping"

    assert len(MyTestModule._events) == 1
    assert MyTestModule._events[0] == ("on_player_join", "on_player_join")

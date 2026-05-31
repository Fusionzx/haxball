import asyncio
from haxball_py import HaxballConfig
from haxball_py.extended import HaxballClientExtended
from haxball_py.module import Module, module, module_command, event
from haxball_py.command import CommandExecInfo
from haxball_py.player import Player


_CIRCLE = {0: "🟢", 1: "🔴", 2: "🔵"}
_LABEL = {0: "SPEC", 1: "RED", 2: "BLUE"}
_COLOR = {0: 0x32CD32, 1: 0xDB7093, 2: 0xADD8E6}


def _teamchat(player: Player, text: str) -> None:
    room = player.room
    if room is None:
        return
    team = player.team
    targets = {0: room.players.spectators(), 1: room.players.red(), 2: room.players.blue()}
    msg = f"[{_CIRCLE.get(team, '🟢')} {_LABEL.get(team, 'SPEC')} CHAT] {player.name}: {text}"
    color = _COLOR.get(team, 0x32CD32)
    for p in targets.get(team, room.players.spectators()).values():
        p.reply(msg, color=color)


@module
class AdminModule(Module):
    @module_command(name="adm", aliases=["admin"], usage="adm", desc="Claims admin status", roles=[])
    async def claim_admin(self, info: CommandExecInfo):
        if info.player.admin:
            info.player.reply("You are already an admin!", color=0xFFFF00)
            return
        info.player.admin = True
        info.player.reply("You are now an administrator!", color=0x00FF00)

    @module_command(name="t", aliases=["teamchat", "tc"], usage="t <message>", desc="Sends a message to your team", roles=[])
    async def team_chat(self, info: CommandExecInfo):
        if not info.arguments:
            info.player.reply("Usage: !t <message>", color=0xFFFF00)
            return
        _teamchat(info.player, " ".join(a.raw for a in info.arguments))

    @event
    async def on_player_join(self, player: Player):
        player.reply(f"Welcome to the room, {player.name}!", color=0x00FFFF)

    @event
    async def on_player_leave(self, player: Player):
        player.reply(f"Goodbye, {player.name}!", color=0xFF0000)


async def main():
    config = HaxballConfig(
        room_name="Extended Haxball Room",
        player_name="BotExtended",
        max_players=10,
        public=False,
        no_player=False,
        headless=True,
        prefix="!",
    )

    client = HaxballClientExtended()
    room = await client.init(config)
    room.module(AdminModule)

    room.set_stadium("Big")
    await room.native.set_score_limit(5)
    await room.native.set_time_limit(0)

    try:
        await room.native.wait_for_room_link(timeout=120)
    except TimeoutError:
        print("Timeout waiting for room link", flush=True)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    asyncio.run(main())

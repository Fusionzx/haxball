import asyncio
from haxball_py import HaxballConfig
from haxball_py.extended import HaxballClientExtended
from haxball_py.module import Module, module, module_command, event
from haxball_py.command import CommandExecInfo
from haxball_py.player import Player

@module
class AdminModule(Module):
    @module_command(name="adm", usage="adm", desc="Claims admin status", roles=[])
    async def claim_admin(self, info: CommandExecInfo):
        info.player.admin = True
        await info.room.native.set_player_admin(info.player.id, True)
        info.player.reply("You are now an administrator!", color=0x00FF00)

    @event
    async def on_player_join(self, player: Player):
        self.room.send(f"Welcome to the room, {player.name}!", color=0x00FFFF)

    @event
    async def on_player_leave(self, player: Player):
        self.room.send(f"Goodbye, {player.name}!", color=0xFF0000)


async def main():
    config = HaxballConfig(
        room_name="Extended Haxball Room",
        player_name="BotExtended",
        max_players=10,
        public=False,
        no_player=False,
        headless=True
    )

    client = HaxballClientExtended()
    room = await client.init(config)
    room.module(AdminModule)

    @room.native.on_room_link
    def on_link(url: str):
        print("room link:", url)

    await room.native.set_default_stadium("Big")
    await room.native.set_score_limit(5)
    await room.native.set_time_limit(0)

    print("Waiting for room link (timeout 120s)...")
    try:
        link = await room.native.wait_for_room_link(timeout=120)
        print(f"Room ready! Link: {link}", flush=True)
    except TimeoutError:
        print("Timeout waiting for room link", flush=True)

    print("Extended room running. Press Ctrl+C to exit.", flush=True)
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

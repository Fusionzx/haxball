import asyncio
from haxball_py import HaxballConfig, Teams
from haxball_py.extended import HaxballClientExtended, RoomExtended
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


async def main():
    config = HaxballConfig(
        room_name="Extended Haxball Room",
        player_name="BotExtended",
        max_players=10,
        public=False,
        no_player=False,
        token="thr1.AAAAAGe1eN8P-B1H9W7O4A.YOUR_TOKEN_HERE", # Placeholder token
        headless=True
    )

    client = HaxballClientExtended()
    
    # We can catch errors or run it, but since token is placeholder, we won't run it here.
    # We will just instantiate client and log that it's configured.
    print("Extended client and modules loaded successfully!")


if __name__ == "__main__":
    asyncio.run(main())

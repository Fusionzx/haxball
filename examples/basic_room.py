import asyncio
import os

from haxball_py import HaxballClient, HaxballConfig


async def main() -> None:
    async with HaxballClient() as client:
        room = await client.init(
            HaxballConfig(
                room_name="Haxball.Py",
                player_name="Bot",
                max_players=16,
                public=False,
                no_player=True,
                token=os.environ.get("HAXBALL_TOKEN"),
            )
        )

        @room.on_player_join
        def on_join(player):
            print(f"join: {player.id} {player.name}")

        @room.on_player_leave
        def on_leave(player):
            print(f"leave: {player.id} {player.name}")

        @room.on_room_link
        def on_link(url: str):
            print("room link:", url)

        await room.set_default_stadium("Big")
        await room.set_score_limit(5)
        await room.set_time_limit(0)

        print("players:", await room.get_player_list())
        print("waiting for link...")
        print(await room.wait_for_room_link(timeout=180))


if __name__ == "__main__":
    asyncio.run(main())

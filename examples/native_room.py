"""Complete native engine test — initializes HaxBall and creates a room."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from haxball._hbinit import HaxballJS


async def main():
    token = os.environ.get("HAXBALL_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]

    room_config = {
        "roomName": "Haxball.Py Native Engine",
        "maxPlayers": 16,
        "public": False,
        "noPlayer": True,
    }
    if token:
        room_config["token"] = token

    print("\n[1/3] Initializing native engine...", flush=True)
    HBInit = await HaxballJS({"debug": True})
    print(f"[OK] HBInit obtained: callable={callable(HBInit)}", flush=True)

    print("\n[2/3] Creating room...", flush=True)
    room = await HBInit(room_config)
    print(f"[OK] Room created: {type(room).__name__}", flush=True)

    print("\n[3/3] Setting up events...", flush=True)

    @room.on_room_link
    def on_link(url):
        print(f"\n>>> ROOM LINK: {url} <<<", flush=True)

    @room.on_player_join
    def on_join(player):
        print(f"Player joined: {player.name} (id={player.id})", flush=True)

    @room.on_player_leave
    def on_leave(player):
        print(f"Player left: {player.name} (id={player.id})", flush=True)

    @room.on_player_chat
    def on_chat(player, msg):
        print(f"{player.name}: {msg}", flush=True)

    await room.set_default_stadium("Big")
    await room.set_score_limit(5)
    await room.set_time_limit(0)

    print("Waiting for room link (timeout 120s)...", flush=True)
    try:
        link = await room.wait_for_room_link(timeout=120)
        print(f"Room ready! Link: {link}", flush=True)
    except TimeoutError:
        print("Timeout waiting for room link", flush=True)

    print("\nRoom running. Press Ctrl+C to exit.", flush=True)
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

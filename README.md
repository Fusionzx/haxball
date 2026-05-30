# haxball-py

A faithful Python bridge for the official HaxBall Headless Host API.

## Why this architecture

The official headless host is controlled through JavaScript in the browser, and state-changing API
calls are asynchronous. This project keeps the official host intact and drives it from Python with
Playwright, which is the most faithful way to reproduce the JS host behavior in Python.

## Install

```bash
pip install -e .
playwright install chromium
```

## Quick start

```python
import asyncio
from haxball_py import HaxballClient, HaxballConfig

async def main():
    client = HaxballClient()
    async with client:
        room = await client.init(HaxballConfig(
            room_name="Haxball.Py",
            player_name="Bot",
            max_players=16,
            public=True,
            no_player=True,
            token="YOUR_TOKEN",
        ))

        @room.on_player_join
        def on_join(player):
            print("joined:", player.name)

        @room.on_room_link
        def on_link(url: str):
            print("room link:", url)

        await room.set_default_stadium("Big")
        await room.set_score_limit(5)
        await room.set_time_limit(0)

        print(await room.get_player_list())
        await asyncio.sleep(3600)

asyncio.run(main())
```

## Design

- `HaxballClient` owns the browser lifecycle.
- `Room` mirrors the official `RoomObject`.
- `EventEmitter` dispatches room events into Python.
- `models.py` contains typed room/player payloads.
- `browser.py` contains the Playwright bridge and JS bootstrap.

## Notes

- A valid HaxBall token is required.
- `no_player=True` is recommended, matching the official docs.
- `proxy_server` is supported through Playwright browser context proxy settings.
- Browser arguments can be passed to disable WebRTC local IP anonymization when needed on VPS.

## Compatibility

Implemented methods include the common room controls from the official headless host API:
`send_chat`, `set_player_admin`, `set_player_team`, `kick_player`, `set_score_limit`,
`set_time_limit`, `set_default_stadium`, `set_custom_stadium`, `set_teams_lock`,
`set_team_colors`, `start_game`, `stop_game`, `pause_game`, `get_player`,
`get_player_list`, `get_scores`, `clear_ban`, `clear_bans`, `set_password`,
`set_require_recaptcha`, `reorder_players`, `send_announcement`, `set_kick_rate_limit`,
`set_player_avatar`, `set_disc_properties`, `get_disc_properties`,
`set_player_disc_properties`, `get_player_disc_properties`, and `get_disc_count`.

Supported events include:
`on_player_join`, `on_player_leave`, `on_team_victory`, `on_player_chat`,
`on_player_ball_kick`, `on_team_goal`, `on_game_start`, `on_game_stop`,
`on_player_admin_change`, `on_player_team_change`, `on_player_kicked`,
`on_game_tick`, `on_game_pause`, `on_game_unpause`, `on_positions_reset`,
`on_player_activity`, `on_stadium_change`, `on_room_link`,
`on_kick_rate_limit_set`, and `on_teams_lock_change`.

This is a wrapper over the official host, not a modified HaxBall runtime.

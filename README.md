# ⚽ haxball

> A faithful, type-safe Python bridge for the official HaxBall Headless Host API.

Drive a real HaxBall headless room from Python using Playwright. No reverse-engineering, no modified runtimes — just the official JavaScript host, automated from Python.

[Português](./README.pt.md) | [Español](./README.es.md)

---

## ✨ Features

- **Three API layers** — choose your abstraction level:
  - **Native** — raw `HBInit` calls, maximum control
  - **Room** — async Python methods mirroring the official `RoomObject` API
  - **Extended** — high-level module/command system with player management
- **Full event system** — all 19 official events with Python callbacks (sync or async)
- **Type-safe** — Pydantic models for players, scores, disc properties, and config
- **Automatic token prompt** — `init()` asks for token interactively if not provided
- **Playwright-based** — reliable browser automation, works headlessly on VPS
- **Disc property reflection** — read/write physics properties of any disc in the game

---

## 📦 Installation

```bash
pip install haxball
playwright install chromium
```

### 📋 Requirements

- Python 3.10+
- Playwright 1.50+
- Pydantic 2.7+

---

## 🚀 Quick Start

### 🏟️ Basic Room

```python
import asyncio
from haxball_py import HaxballClient, HaxballConfig

async def main():
    async with HaxballClient() as client:
        room = await client.init(HaxballConfig(
            room_name="Haxball.Py",
            player_name="Bot",
            max_players=16,
            public=False,
            no_player=True,
        ))

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
        await room.wait_for_room_link(timeout=180)
        await asyncio.sleep(3600)

asyncio.run(main())
```

### 🔌 Extended Room (Modules & Commands)

```python
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
        info.player.reply("You are now an administrator!", color=0x00FF00)

    @event
    async def on_player_join(self, player: Player):
        await self.room.send(f"Welcome to the room, {player.name}!", color=0x00FFFF)

    @event
    async def on_player_leave(self, player: Player):
        await self.room.send(f"Goodbye, {player.name}!", color=0xFF0000)

async def main():
    config = HaxballConfig(
        room_name="Extended Haxball Room",
        player_name="BotExtended",
        max_players=10,
        public=False,
        no_player=False,
        headless=True,
    )

    client = HaxballClientExtended()
    room = await client.init(config)
    room.module(AdminModule)

    @room.native.on_room_link
    def on_link(url: str):
        print("room link:", url)

    room.set_stadium("Big")
    await room.native.set_score_limit(5)
    await room.native.set_time_limit(0)

    print(await room.native.wait_for_room_link(timeout=120))
    await asyncio.sleep(3600)

asyncio.run(main())
```

### ⚡ Native Engine (Raw HBInit)

```python
import asyncio
from haxball_py._hbinit import HaxballJS

async def main():
    HBInit = await HaxballJS({"debug": True})
    room = await HBInit({
        "roomName": "Haxball.Py Native Engine",
        "maxPlayers": 16,
        "public": False,
        "noPlayer": True,
    })

    @room.on_room_link
    def on_link(url):
        print(f">>> ROOM LINK: {url} <<<")

    @room.on_player_join
    def on_join(player):
        print(f"Player joined: {player.name} (id={player.id})")

    @room.on_player_leave
    def on_leave(player):
        print(f"Player left: {player.name} (id={player.id})")

    await room.set_default_stadium("Big")
    await room.set_score_limit(5)
    await room.set_time_limit(0)

    await room.wait_for_room_link(timeout=120)
    await asyncio.sleep(3600)

asyncio.run(main())
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│              Your Python Code            │
├─────────────────────────────────────────┤
│    Room        RoomExtended    HBInit    │  ← API layers
├─────────────────────────────────────────┤
│           BrowserBridge                  │  ← Playwright automation
├─────────────────────────────────────────┤
│      Playwright (Chromium)               │  ← Browser engine
├─────────────────────────────────────────┤
│      HaxBall Headless Host (JS)          │  ← Official runtime
└─────────────────────────────────────────┘
```

The project respects the official HaxBall headless host as the single source of truth. All API calls are forwarded as-is to the JavaScript `RoomObject` via Playwright's `evaluate()`, and events are bridged back through a message-passing channel injected into the page.

---

## ⚙️ Configuration Reference

### ⚙️ `HaxballConfig`

| Field | Type | Default | Description |
|---|---|---|---|
| `room_name` (alias `roomName`) | `str` | required | Room display name |
| `player_name` (alias `playerName`) | `str \| None` | `None` | Bot player name (auto-set if `no_player=False`) |
| `password` | `str \| None` | `None` | Room password |
| `max_players` (alias `maxPlayers`) | `int` | `16` | Max players (1–50) |
| `public` | `bool` | `True` | Whether the room appears in the lobby |
| `no_player` (alias `noPlayer`) | `bool` | `True` | Whether the host joins as a player |
| `token` | `str` | required (prompted) | HaxBall authentication token |
| `geo` | `GeoConfig \| None` | `None` | Geolocation override |
| `prefix` | `str` | `"!"` | Extended API command prefix |
| `proxy_server` | `str \| None` | `None` | HTTP proxy for the browser |
| `headless` | `bool` | `True` | Run browser headless |
| `browser_executable_path` | `str \| None` | `None` | Custom Chromium path |
| `browser_channel` | `str \| None` | `None` | Browser channel (e.g., `"chrome"`) |
| `browser_args` | `list[str]` | `[]` | Extra Chromium CLI args |
| `timeout_ms` | `int` | `30000` | Browser operation timeout |
| `headless_host_url` | `str` | `https://html5.haxball.com/headless` | Headless host URL |

### 🌍 `GeoConfig`

| Field | Type | Default |
|---|---|---|
| `code` | `str` | `"xx"` |
| `lat` | `float` | `0.0` |
| `lon` | `float` | `0.0` |

---

## 🛠️ Room API

### 📡 Methods

All methods return `Any` (the JSON-decoded result from the JS host).

| Python method | JS equivalent | Description |
|---|---|---|
| `send_chat(message, target_id?)` | `sendChat` | Send a chat message |
| `set_player_admin(id, admin)` | `setPlayerAdmin` | Grant/revoke admin |
| `set_player_team(id, team)` | `setPlayerTeam` | Set player's team (0=spec, 1=red, 2=blue) |
| `kick_player(id, reason?, ban?)` | `kickPlayer` | Kick or ban a player |
| `clear_ban(id)` | `clearBan` | Clear ban for a player |
| `clear_bans()` | `clearBans` | Clear all bans |
| `set_score_limit(limit)` | `setScoreLimit` | Set goals to win |
| `set_time_limit(minutes)` | `setTimeLimit` | Set match time limit |
| `set_default_stadium(name)` | `setDefaultStadium` | Set stadium by name |
| `set_custom_stadium(contents)` | `setCustomStadium` | Set custom stadium (HBS) |
| `set_teams_lock(locked)` | `setTeamsLock` | Lock/unlock teams |
| `set_team_colors(team, angle, text, colors)` | `setTeamColors` | Set team colors |
| `start_game()` | `startGame` | Start the match |
| `stop_game()` | `stopGame` | Stop the match |
| `pause_game(state)` | `pauseGame` | Pause/unpause |
| `get_player(id)` → `Player \| None` | `getPlayer` | Get player info |
| `get_player_list()` → `list[Player]` | `getPlayerList` | Get all players |
| `get_scores()` → `Scores \| None` | `getScores` | Get scoreboard |
| `set_password(password)` | `setPassword` | Set/clear room password |
| `set_require_recaptcha(required)` | `setRequireRecaptcha` | Toggle recaptcha |
| `reorder_players(ids)` | `reorderPlayers` | Reorder player list |
| `send_announcement(msg, color?, style?)` | `sendAnnouncement` | Send colored announcement |
| `set_kick_rate_limit(min, rate, burst, by?)` | `setKickRateLimit` | Configure kick rate limits |
| `set_player_avatar(id, avatar)` | `setPlayerAvatar` | Set player avatar |
| `set_disc_properties(id, props)` | `setDiscProperties` | Set disc physics |
| `get_disc_properties(id)` → `DiscProperties` | `getDiscProperties` | Get disc physics |
| `set_player_disc_properties(id, props)` | `setPlayerDiscProperties` | Set player's disc physics |
| `get_player_disc_properties(id)` → `DiscProperties` | `getPlayerDiscProperties` | Get player's disc physics |
| `get_disc_count()` → `int` | `getDiscCount` | Total disc count |
| `wait_for_room_link(timeout?)` → `str` | — | Blocks until the room link is available |

### 🔔 Events

| Python event | JS event | Payload |
|---|---|---|
| `on_player_join` | `onPlayerJoin` | `Player` |
| `on_player_leave` | `onPlayerLeave` | `Player` |
| `on_team_victory` | `onTeamVictory` | `Scores` |
| `on_player_chat` | `onPlayerChat` | `Player`, `str` (message) |
| `on_player_ball_kick` | `onPlayerBallKick` | `Player` |
| `on_team_goal` | `onTeamGoal` | `int` (team) |
| `on_game_start` | `onGameStart` | `Player` (byPlayer) |
| `on_game_stop` | `onGameStop` | `Player` (byPlayer) |
| `on_player_admin_change` | `onPlayerAdminChange` | `Player`, `bool` (admin) |
| `on_player_team_change` | `onPlayerTeamChange` | `Player`, `int` (team) |
| `on_player_kicked` | `onPlayerKicked` | `Player`, `str` (reason), `bool` (ban) |
| `on_game_tick` | `onGameTick` | — |
| `on_game_pause` | `onGamePause` | `bool` (paused) |
| `on_game_unpause` | `onGameUnpause` | — |
| `on_positions_reset` | `onPositionsReset` | — |
| `on_player_activity` | `onPlayerActivity` | `Player` |
| `on_stadium_change` | `onStadiumChange` | `str` (stadium name) |
| `on_room_link` | `onRoomLink` | `str` (URL) |
| `on_kick_rate_limit_set` | `onKickRateLimitSet` | `int` (min), `int` (rate), `int` (burst) |
| `on_teams_lock_change` | `onTeamsLockChange` | `bool` (locked) |

Events can be bound via decorator or direct assignment:

```python
# Decorator (preferred)
@room.on_player_join
def handler(player):
    pass

# Assignment
room.on_player_join = lambda p: print(p.name)
```

Both sync and async callbacks are supported.

---

## 🔌 Extended API

The `HaxballClientExtended` / `RoomExtended` layer adds a modern, intuitive API on top of the native room:

### Live Properties

Instead of calling verbose methods on the native room, you interact directly with **Player** and **Disc** objects:

| What | Old way | New way |
|---|---|---|
| Grant admin | `await room.set_player_admin(id, True)` | `player.admin = True` |
| Move team | `await room.set_player_team(id, 1)` | `player.team = 1` |
| Change radius | `await room.set_player_disc_properties(id, {"radius": 15})` | `player.radius = 15` |
| Kick player | `await room.kick_player(id, "bye")` | `player.kick("bye")` |
| Ban player | `await room.kick_player(id, "spam", True)` | `player.ban("spam")` |
| Send whisper | `await room.send_chat("hi", id)` | `player.reply("hi")` |
| Set disc physics | `await room.set_disc_properties(id, {...})` | `disc.x = 10; disc.radius = 5` |
| Get IP | — | `player.ip` |

### Player Properties

| Property | Type | Description |
|---|---|---|
| `player.id` | `int` | Player's unique ID (read-only) |
| `player.name` | `str` | Player's name (read-only) |
| `player.admin` | `bool` | Get/set admin status |
| `player.team` | `int` | Get/set team (0=spec, 1=red, 2=blue) |
| `player.auth` | `str \| None` | Public ID (read-only) |
| `player.conn` | `str \| None` | Connection identifier (read-only) |
| `player.ip` | `str \| None` | Decoded IP address (read-only) |
| `player.position` | `Position \| None` | Get/set position on the map |
| `player.roles` | `list` | Permission roles |

### Disc Properties (also on Player)

`player.x`, `player.y`, `player.radius`, `player.xspeed`, `player.yspeed`, `player.xgravity`, `player.ygravity`, `player.b_coeff`, `player.inv_mass`, `player.damping`, `player.c_mask`, `player.c_group`, `player.color`

Setting any of these immediately syncs to the native room.

### RoomExtended Methods

| Method | Description |
|---|---|
| `room.send(msg, color?, style?, target_id?)` | Send announcement or whisper |
| `room.set_stadium(name \| dict)` | Set stadium (name or HBS JSON) |
| `room.lock_teams()` / `room.unlock_teams()` | Lock/unlock team switching |
| `room.enable_captcha()` / `room.disable_captcha()` | Toggle captcha requirement |
| `room.start()` / `room.stop()` | Start/stop the game |
| `room.pause()` / `room.unpause()` | Pause/unpause the game |
| `room.start_recording()` / `await room.stop_recording()` | Replay recording |
| `room.unban(id)` / `room.unban_all()` | Unban players |
| `room.clear_password()` / `room.password = "..."` | Room password management |
| `await room.is_game_in_progress()` | Check if a match is running |
| `await room.scores` | Get current scores |
| `await room.ball` | Get the ball disc (Disc object with live props) |
| `room.command(options)` | Register a command |
| `room.remove_command(name)` | Remove a command |
| `room.module(ModuleClass)` | Load a module |

### Private Messages

```python
await room.send("Only player #3 can see this", target_id=3)
player.reply("Only this player can see this")
```

`player.reply(...)` is a convenience wrapper for `room.send(..., target_id=player.id)`.

### Logging and Hidden Commands

Extended rooms log room events with `RoomLogger` by default. Disable this with
`room.logging = False`, or use `RoomLogger().log_event(...)` directly when you
need the same formatting outside a room.

Commands registered with `room.command(...)` or `@module_command(...)` hide the
player's original chat message by default, including configured single-character
commands sent without the prefix, such as `t hello`. Pass `delete_message=False`
to leave a command message visible.

### 📦 Module Example

```python
from haxball_py.module import Module, module, module_command, event

@module
class MyModule(Module):
    @event
    async def on_player_join(self, player):
        await self.room.send(f"Welcome, {player.name}!")

    @module_command(name="ping", usage="ping", desc="Pong!", delete_message=False)
    async def ping(self, info):
        info.player.reply("Pong!")
```

---

## ⚡ Native Engine

The native engine (`HaxballJS`) is a thin wrapper that obtains the `HBInit` function from the HaxBall page and exposes it as a Python callable. This is the lowest-level API — you pass the exact same object you would pass in JavaScript.

```python
from haxball_py._hbinit import HaxballJS

HBInit = await HaxballJS({"debug": True})
room = await HBInit({"roomName": "...", "maxPlayers": 16, ...})
```

The returned `room` object mirrors the JS `RoomObject` — it has the same methods, events, and behavior. Python names are already mapped to their JS equivalents (e.g., `set_default_stadium` → `setDefaultStadium`).

---

## 🐛 Error Handling

### ❌ `HaxballBridgeError`

Raised when communication with the browser fails (timeout, crash, etc.).

### ⏰ `HaxballTimeoutError`

Raised when a browser operation exceeds the configured timeout.

### 💡 Example

```python
from haxball_py.errors import HaxballBridgeError

try:
    room = await client.init(config)
except HaxballBridgeError as e:
    print(f"Bridge error: {e}")
```

---

## ✅ Compatibility

### 📋 Implemented Methods

`send_chat`, `set_player_admin`, `set_player_team`, `kick_player`, `set_score_limit`, `set_time_limit`, `set_default_stadium`, `set_custom_stadium`, `set_teams_lock`, `set_team_colors`, `start_game`, `stop_game`, `pause_game`, `get_player`, `get_player_list`, `get_scores`, `clear_ban`, `clear_bans`, `set_password`, `set_require_recaptcha`, `reorder_players`, `send_announcement`, `set_kick_rate_limit`, `set_player_avatar`, `set_disc_properties`, `get_disc_properties`, `set_player_disc_properties`, `get_player_disc_properties`, `get_disc_count`

### 📝 Notes

- A valid HaxBall token is **required** (you can get one at https://www.haxball.com/headless)
- `no_player=True` is recommended when running 24/7 bots
- Proxy support is available through `proxy_server` in the config
- Browser args (e.g., `--disable-web-security`) can be passed via `browser_args`

---

## 🧪 Development

```bash
git clone https://github.com/Fusionzx/haxball
cd haxball
pip install -e ".[dev]"
playwright install chromium
ruff check .
pytest
```

---

## 📄 License

This project is a wrapper around the official HaxBall Headless Host API. It is not affiliated with or endorsed by HaxBall.

© 2026 haxball contributors

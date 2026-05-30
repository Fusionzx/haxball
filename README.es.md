# haxball.py

> Un puente fiel y tipado para la API oficial de HaxBall Headless Host.

Controla una sala headless real de HaxBall desde Python usando Playwright. Sin ingeniería inversa ni runtimes modificados — el host oficial de JavaScript, automatizado desde Python.

[English](./README.md) | [Português](./README.pt.md)

---

## Características

- **Tres capas de API** — elige tu nivel de abstracción:
  - **Native** — llamadas `HBInit` puras, máximo control
  - **Room** — métodos asíncronos que reflejan la API oficial `RoomObject`
  - **Extended** — sistema de módulos/comandos de alto nivel con gestión de jugadores
- **Sistema completo de eventos** — los 19 eventos oficiales con callbacks en Python (síncronos o asíncronos)
- **Tipado seguro** — modelos Pydantic para jugadores, puntuaciones, propiedades de discos y configuración
- **Solicitud automática de token** — `init()` pide el token interactivamente si no se proporciona
- **Basado en Playwright** — automatización fiable del navegador, funciona sin cabeza en VPS
- **Reflexión de propiedades de discos** — lee/escribe propiedades físicas de cualquier disco en el juego

---

## Instalación

```bash
pip install haxball-py
playwright install chromium
```

### Requisitos

- Python 3.10+
- Playwright 1.50+
- Pydantic 2.7+

---

## Inicio Rápido

### Sala Básica

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

### Sala Extendida (Módulos y Comandos)

```python
import asyncio
from haxball_py import HaxballConfig
from haxball_py.extended import HaxballClientExtended
from haxball_py.module import Module, module, module_command, event
from haxball_py.command import CommandExecInfo
from haxball_py.player import Player

@module
class AdminModule(Module):
    @module_command(name="adm", usage="adm", desc="Obtener administrador", roles=[])
    async def claim_admin(self, info: CommandExecInfo):
        info.player.admin = True
        await info.room.native.set_player_admin(info.player.id, True)
        info.player.reply("¡Ahora eres administrador!", color=0x00FF00)

    @event
    async def on_player_join(self, player: Player):
        self.room.send(f"¡Bienvenido a la sala, {player.name}!", color=0x00FFFF)

    @event
    async def on_player_leave(self, player: Player):
        self.room.send(f"¡Hasta luego, {player.name}!", color=0xFF0000)

async def main():
    config = HaxballConfig(
        room_name="Sala Extendida Haxball",
        player_name="BotExtendido",
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

    await room.native.set_default_stadium("Big")
    await room.native.set_score_limit(5)
    await room.native.set_time_limit(0)

    print(await room.native.wait_for_room_link(timeout=120))
    await asyncio.sleep(3600)

asyncio.run(main())
```

### Motor Nativo (HBInit Puro)

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
        print(f">>> ENLACE DE SALA: {url} <<<")

    @room.on_player_join
    def on_join(player):
        print(f"Jugador conectado: {player.name} (id={player.id})")

    @room.on_player_leave
    def on_leave(player):
        print(f"Jugador desconectado: {player.name} (id={player.id})")

    await room.set_default_stadium("Big")
    await room.set_score_limit(5)
    await room.set_time_limit(0)

    await room.wait_for_room_link(timeout=120)
    await asyncio.sleep(3600)

asyncio.run(main())
```

---

## Arquitectura

```
┌─────────────────────────────────────────┐
│              Tu Código Python            │
├─────────────────────────────────────────┤
│    Room        RoomExtended    HBInit    │  ← Capas de API
├─────────────────────────────────────────┤
│           BrowserBridge                  │  ← Automatización Playwright
├─────────────────────────────────────────┤
│      Playwright (Chromium)               │  ← Motor del navegador
├─────────────────────────────────────────┤
│      HaxBall Headless Host (JS)          │  ← Runtime oficial
└─────────────────────────────────────────┘
```

El proyecto respeta el host headless oficial de HaxBall como única fuente de verdad. Todas las llamadas a la API se reenvían tal cual al `RoomObject` de JavaScript a través de `evaluate()` de Playwright, y los eventos se puentean de vuelta mediante un canal de paso de mensajes inyectado en la página.

---

## Referencia de Configuración

### `HaxballConfig`

| Campo | Tipo | Defecto | Descripción |
|---|---|---|---|
| `room_name` (alias `roomName`) | `str` | requerido | Nombre visible de la sala |
| `player_name` (alias `playerName`) | `str \| None` | `None` | Nombre del bot (auto si `no_player=False`) |
| `password` | `str \| None` | `None` | Contraseña de la sala |
| `max_players` (alias `maxPlayers`) | `int` | `16` | Máximo de jugadores (1–50) |
| `public` | `bool` | `True` | Mostrar sala en el lobby |
| `no_player` (alias `noPlayer`) | `bool` | `True` | El host no entra como jugador |
| `token` | `str` | requerido (solicitado) | Token de autenticación de HaxBall |
| `geo` | `GeoConfig \| None` | `None` | Geolocalización personalizada |
| `proxy_server` | `str \| None` | `None` | Proxy HTTP para el navegador |
| `headless` | `bool` | `True` | Ejecutar navegador sin cabeza |
| `browser_executable_path` | `str \| None` | `None` | Ruta personalizada de Chromium |
| `browser_channel` | `str \| None` | `None` | Canal del navegador (ej. `"chrome"`) |
| `browser_args` | `list[str]` | `[]` | Argumentos extra de Chromium |
| `timeout_ms` | `int` | `30000` | Tiempo de espera del navegador |
| `headless_host_url` | `str` | `https://html5.haxball.com/headless` | URL del host headless |

### `GeoConfig`

| Campo | Tipo | Defecto |
|---|---|---|
| `code` | `str` | `"xx"` |
| `lat` | `float` | `0.0` |
| `lon` | `float` | `0.0` |

---

## API de Sala

### Métodos

| Python | JS | Descripción |
|---|---|---|
| `send_chat(message, target_id?)` | `sendChat` | Enviar mensaje de chat |
| `set_player_admin(id, admin)` | `setPlayerAdmin` | Dar/revocar administrador |
| `set_player_team(id, team)` | `setPlayerTeam` | Cambiar equipo (0=spec, 1=red, 2=blue) |
| `kick_player(id, reason?, ban?)` | `kickPlayer` | Expulsar o banear |
| `clear_ban(id)` | `clearBan` | Limpiar ban |
| `clear_bans()` | `clearBans` | Limpiar todos los baneos |
| `set_score_limit(limit)` | `setScoreLimit` | Goles para ganar |
| `set_time_limit(minutes)` | `setTimeLimit` | Límite de tiempo |
| `set_default_stadium(name)` | `setDefaultStadium` | Estadio por nombre |
| `set_custom_stadium(contents)` | `setCustomStadium` | Estadio personalizado (HBS) |
| `set_teams_lock(locked)` | `setTeamsLock` | Bloquear equipos |
| `set_team_colors(team, angle, text, colors)` | `setTeamColors` | Colores de equipo |
| `start_game()` | `startGame` | Iniciar partido |
| `stop_game()` | `stopGame` | Detener partido |
| `pause_game(state)` | `pauseGame` | Pausar/reanudar |
| `get_player(id)` → `Player \| None` | `getPlayer` | Información de jugador |
| `get_player_list()` → `list[Player]` | `getPlayerList` | Todos los jugadores |
| `get_scores()` → `Scores \| None` | `getScores` | Marcador |
| `set_password(password)` | `setPassword` | Contraseña de sala |
| `set_require_recaptcha(required)` | `setRequireRecaptcha` | Activar/desactivar recaptcha |
| `reorder_players(ids)` | `reorderPlayers` | Reordenar lista |
| `send_announcement(msg, color?, style?)` | `sendAnnouncement` | Anuncio coloreado |
| `set_kick_rate_limit(min, rate, burst, by?)` | `setKickRateLimit` | Límite de expulsiones |
| `set_player_avatar(id, avatar)` | `setPlayerAvatar` | Avatar de jugador |
| `set_disc_properties(id, props)` | `setDiscProperties` | Física de disco |
| `get_disc_properties(id)` → `DiscProperties` | `getDiscProperties` | Física de disco |
| `set_player_disc_properties(id, props)` | `setPlayerDiscProperties` | Física del disco del jugador |
| `get_player_disc_properties(id)` → `DiscProperties` | `getPlayerDiscProperties` | Física del disco del jugador |
| `get_disc_count()` → `int` | `getDiscCount` | Total de discos |
| `wait_for_room_link(timeout?)` → `str` | — | Espera hasta obtener el enlace |

### Eventos

| Python | JS | Payload |
|---|---|---|
| `on_player_join` | `onPlayerJoin` | `Player` |
| `on_player_leave` | `onPlayerLeave` | `Player` |
| `on_team_victory` | `onTeamVictory` | `Scores` |
| `on_player_chat` | `onPlayerChat` | `Player`, `str` |
| `on_player_ball_kick` | `onPlayerBallKick` | `Player` |
| `on_team_goal` | `onTeamGoal` | `int` (team) |
| `on_game_start` | `onGameStart` | `Player` |
| `on_game_stop` | `onGameStop` | `Player` |
| `on_player_admin_change` | `onPlayerAdminChange` | `Player`, `bool` |
| `on_player_team_change` | `onPlayerTeamChange` | `Player`, `int` |
| `on_player_kicked` | `onPlayerKicked` | `Player`, `str`, `bool` |
| `on_game_tick` | `onGameTick` | — |
| `on_game_pause` | `onGamePause` | `bool` |
| `on_game_unpause` | `onGameUnpause` | — |
| `on_positions_reset` | `onPositionsReset` | — |
| `on_player_activity` | `onPlayerActivity` | `Player` |
| `on_stadium_change` | `onStadiumChange` | `str` |
| `on_room_link` | `onRoomLink` | `str` |
| `on_kick_rate_limit_set` | `onKickRateLimitSet` | `int`, `int`, `int` |
| `on_teams_lock_change` | `onTeamsLockChange` | `bool` |

---

## API Extendida

La capa `HaxballClientExtended` / `RoomExtended` añade:

- **Gestión de jugadores** — wrapper `Player` con `.reply()`, estado admin, permisos
- **Sistema de comandos** — comandos tipados con acceso basado en roles
- **Sistema de módulos** — clases `Module` conectables con auto-descubrimiento
- **Emisor de eventos** — bus de eventos personalizado para comunicación entre módulos
- **Abstracción de discos** — wrapper `Disc` para propiedades físicas
- **Registro** — registro automático de chat

---

## Desarrollo

```bash
git clone https://github.com/yourusername/haxball.py
cd haxball.py
pip install -e ".[dev]"
playwright install chromium
ruff check .
pytest
```

---

## Licencia

Este proyecto es un wrapper alrededor de la API oficial de HaxBall Headless Host. No está afiliado ni respaldado por HaxBall.

© 2026 contribuyentes de haxball.py

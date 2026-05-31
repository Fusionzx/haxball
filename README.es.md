# ⚽ haxball-python

> Un puente fiel y tipado para la API oficial de HaxBall Headless Host.

Controla una sala headless real de HaxBall desde Python usando Playwright. Sin ingeniería inversa ni runtimes modificados — el host oficial de JavaScript, automatizado desde Python.

[English](./README.md) | [Português](./README.pt.md)

---

## ✨ Características

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

## 📦 Instalación

```bash
pip install haxball-python
playwright install chromium
```

### 📋 Requisitos

- Python 3.10+
- Playwright 1.50+
- Pydantic 2.7+

---

## 🚀 Inicio Rápido

### 🏟️ Sala Básica

```python
import asyncio
from haxball import HaxballClient, HaxBallConfig

async def main():
    async with HaxballClient() as client:
        room = await client.init(HaxBallConfig(
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

### 🔌 Sala Extendida (Módulos y Comandos)

```python
import asyncio
from haxball import HaxBallConfig
from haxball.extended import HaxballClientExtended
from haxball.module import Module, module, module_command, event
from haxball.command import CommandExecInfo
from haxball.player import Player

@module
class AdminModule(Module):
    @module_command(name="adm", aliases=["admin"], usage="adm", desc="Obtener administrador", roles=[])
    async def claim_admin(self, info: CommandExecInfo):
        if info.player.admin:
            info.player.reply("¡Ya eres administrador!", color=0xFFFF00)
            return
        info.player.admin = True
        info.player.reply("¡Ahora eres administrador!", color=0x00FF00)

    @event
    async def on_player_join(self, player: Player):
        await self.room.send(f"¡Bienvenido a la sala, {player.name}!", color=0x00FFFF)

    @event
    async def on_player_leave(self, player: Player):
        await self.room.send(f"¡Hasta luego, {player.name}!", color=0xFF0000)

async def main():
    config = HaxBallConfig(
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

    room.set_stadium("Big")
    await room.native.set_score_limit(5)
    await room.native.set_time_limit(0)

    print(await room.native.wait_for_room_link(timeout=120))
    await asyncio.sleep(3600)

asyncio.run(main())
```

### ⚡ Motor Nativo (HBInit Puro)

```python
import asyncio
from haxball._hbinit import HaxballJS

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

## 🏗️ Arquitectura

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

## ⚙️ Referencia de Configuración

### ⚙️ `HaxBallConfig`

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
| `prefix` | `str` | `"!"` | Prefijo de comandos de la API extendida |
| `proxy_server` | `str \| None` | `None` | Proxy HTTP para el navegador |
| `headless` | `bool` | `True` | Ejecutar navegador sin cabeza |
| `browser_executable_path` | `str \| None` | `None` | Ruta personalizada de Chromium |
| `browser_channel` | `str \| None` | `None` | Canal del navegador (ej. `"chrome"`) |
| `browser_args` | `list[str]` | `[]` | Argumentos extra de Chromium |
| `timeout_ms` | `int` | `30000` | Tiempo de espera del navegador |
| `headless_host_url` | `str` | `https://html5.haxball.com/headless` | URL del host headless |

### 🌍 `GeoConfig`

| Campo | Tipo | Defecto |
|---|---|---|
| `code` | `str` | `"xx"` |
| `lat` | `float` | `0.0` |
| `lon` | `float` | `0.0` |

---

## 🛠️ API de Sala

### 📡 Métodos

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

### 🔔 Eventos

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

## 🔌 API Extendida

La capa `HaxballClientExtended` / `RoomExtended` añade una API moderna e intuitiva sobre la sala nativa.

### Propiedades en Vivo

En lugar de llamar métodos verbosos en la sala nativa, interactúa directamente con objetos **Player** y **Disc**:

| Qué | Forma antigua | Forma nueva |
|---|---|---|
| Dar admin | `await room.set_player_admin(id, True)` | `player.admin = True` |
| Cambiar equipo | `await room.set_player_team(id, 1)` | `player.team = 1` |
| Cambiar radio | `await room.set_player_disc_properties(id, {"radius": 15})` | `player.radius = 15` |
| Expulsar | `await room.kick_player(id, "razón")` | `player.kick("razón")` |
| Banear | `await room.kick_player(id, "spam", True)` | `player.ban("spam")` |
| Mensaje privado | `await room.send_chat("hola", id)` | `player.reply("hola")` |
| Física del disco | `await room.set_disc_properties(id, {...})` | `disc.x = 10; disc.radius = 5` |
| Obtener IP | — | `player.ip` |

### Propiedades del Player

| Propiedad | Tipo | Descripción |
|---|---|---|
| `player.id` | `int` | ID único (solo lectura) |
| `player.name` | `str` | Nombre del jugador (solo lectura) |
| `player.admin` | `bool` | Obtener/establecer admin |
| `player.team` | `int` | Obtener/establecer equipo (0=spec, 1=red, 2=blue) |
| `player.auth` | `str \| None` | ID pública (solo lectura) |
| `player.conn` | `str \| None` | Identificador de conexión (solo lectura) |
| `player.ip` | `str \| None` | Dirección IP decodificada (solo lectura) |
| `player.position` | `Position \| None` | Obtener/establecer posición en el mapa |
| `player.roles` | `list` | Roles de permiso |

### Propiedades del Disc (también en Player)

`player.x`, `player.y`, `player.radius`, `player.xspeed`, `player.yspeed`, `player.xgravity`, `player.ygravity`, `player.b_coeff`, `player.inv_mass`, `player.damping`, `player.c_mask`, `player.c_group`, `player.color`

Cualquier cambio en estas propiedades se sincroniza inmediatamente con la sala nativa.

### Métodos de RoomExtended

| Método | Descripción |
|---|---|
| `room.send(msg, color?, style?, target_id?)` | Enviar anuncio o mensaje privado |
| `room.set_stadium(nombre \| dict)` | Establecer estadio (nombre o HBS JSON) |
| `room.lock_teams()` / `room.unlock_teams()` | Bloquear/desbloquear equipos |
| `room.enable_captcha()` / `room.disable_captcha()` | Activar/desactivar captcha |
| `room.start()` / `room.stop()` | Iniciar/detener partida |
| `room.pause()` / `room.unpause()` | Pausar/reanudar partida |
| `room.start_recording()` / `await room.stop_recording()` | Grabación de replay |
| `room.unban(id)` / `room.unban_all()` | Desbanear jugadores |
| `room.clear_password()` / `room.password = "..."` | Gestionar contraseña de sala |
| `await room.is_game_in_progress()` | Verificar si hay partida en curso |
| `await room.scores` | Obtener puntuaciones actuales |
| `await room.ball` | Obtener el disco de la bola (Disc con props en vivo) |
| `room.command(options)` | Registrar un comando |
| `room.remove_command(nombre)` | Eliminar un comando |
| `room.module(ModuleClass)` | Cargar un módulo |

### Mensajes Privados

```python
await room.send("Solo el jugador #3 puede ver esto", target_id=3)
player.reply("Solo este jugador puede ver esto")
```

`player.reply(...)` es un atajo para `room.send(..., target_id=player.id)`.

### Logging y Comandos Ocultos

Las salas extendidas registran eventos con `RoomLogger` de forma predeterminada.
Desactívalo con `room.logging = False`, o usa `RoomLogger().log_event(...)`
directamente si necesitas el mismo formato fuera de una sala.

Los comandos registrados con `room.command(...)` o `@module_command(...)`
ocultan el mensaje original del jugador por defecto, incluso los comandos
configurados de un solo carácter enviados sin prefijo, como `t hola`. Usa
`delete_message=False` para mantener visible el mensaje de un comando.

---

## 🧪 Desarrollo

```bash
git clone https://github.com/Fusionzx/haxball-python
cd haxball-python
pip install -e ".[dev]"
playwright install chromium
ruff check .
pytest
```

---

## 📄 Licencia

Este proyecto es un wrapper alrededor de la API oficial de HaxBall Headless Host. No está afiliado ni respaldado por HaxBall.

Consulta la [licencia MIT](./LICENSE), la [guía de contribución](./CONTRIBUTING.md),
el [código de conducta](./CODE_OF_CONDUCT.md) y la [política de seguridad](./SECURITY.md).

© 2026 contribuyentes de haxball-python

# ⚽ haxball.py

> Uma ponte Python fiel e com tipagem segura para a API oficial do HaxBall Headless Host.

Controle uma sala headless real do HaxBall a partir do Python usando Playwright. Sem engenharia reversa ou runtimes modificados — o host oficial JavaScript, automatizado a partir do Python.

[English](./README.md) | [Español](./README.es.md)

---

## ✨ Funcionalidades

- **Três camadas de API** — escolha seu nível de abstração:
  - **Native** — chamadas `HBInit` puras, máximo controle
  - **Room** — métodos assíncronos que espelham a API oficial `RoomObject`
  - **Extended** — sistema de módulos/comandos de alto nível com gerenciamento de jogadores
- **Sistema completo de eventos** — todos os 19 eventos oficiais com callbacks em Python (síncronos ou assíncronos)
- **Tipagem segura** — modelos Pydantic para jogadores, pontuações, propriedades de discos e configuração
- **Solicitação automática de token** — `init()` pede o token interativamente se não fornecido
- **Baseado no Playwright** — automação confiável do navegador, funciona headless em VPS
- **Reflexão de propriedades de discos** — leia/escreva propriedades físicas de qualquer disco no jogo

---

## 📦 Instalação

```bash
pip install haxball-py
playwright install chromium
```

### 📋 Requisitos

- Python 3.10+
- Playwright 1.50+
- Pydantic 2.7+

---

## 🚀 Início Rápido

### 🏟️ Sala Básica

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

### 🔌 Sala Estendida (Módulos e Comandos)

```python
import asyncio
from haxball_py import HaxballConfig
from haxball_py.extended import HaxballClientExtended
from haxball_py.module import Module, module, module_command, event
from haxball_py.command import CommandExecInfo
from haxball_py.player import Player

@module
class AdminModule(Module):
    @module_command(name="adm", usage="adm", desc="Obter administrador", roles=[])
    async def claim_admin(self, info: CommandExecInfo):
        info.player.admin = True
        await info.room.native.set_player_admin(info.player.id, True)
        info.player.reply("Agora você é administrador!", color=0x00FF00)

    @event
    async def on_player_join(self, player: Player):
        self.room.send(f"Bem-vindo à sala, {player.name}!", color=0x00FFFF)

    @event
    async def on_player_leave(self, player: Player):
        self.room.send(f"Até logo, {player.name}!", color=0xFF0000)

async def main():
    config = HaxballConfig(
        room_name="Sala Estendida Haxball",
        player_name="BotEstendido",
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

### ⚡ Motor Nativo (HBInit Puro)

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
        print(f">>> LINK DA SALA: {url} <<<")

    @room.on_player_join
    def on_join(player):
        print(f"Jogador entrou: {player.name} (id={player.id})")

    @room.on_player_leave
    def on_leave(player):
        print(f"Jogador saiu: {player.name} (id={player.id})")

    await room.set_default_stadium("Big")
    await room.set_score_limit(5)
    await room.set_time_limit(0)

    await room.wait_for_room_link(timeout=120)
    await asyncio.sleep(3600)

asyncio.run(main())
```

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────┐
│              Seu Código Python           │
├─────────────────────────────────────────┤
│    Room        RoomExtended    HBInit    │  ← Camadas da API
├─────────────────────────────────────────┤
│           BrowserBridge                  │  ← Automação Playwright
├─────────────────────────────────────────┤
│      Playwright (Chromium)               │  ← Motor do navegador
├─────────────────────────────────────────┤
│      HaxBall Headless Host (JS)          │  ← Runtime oficial
└─────────────────────────────────────────┘
```

O projeto respeita o host headless oficial do HaxBall como única fonte de verdade. Todas as chamadas à API são encaminhadas diretamente para o `RoomObject` JavaScript via `evaluate()` do Playwright, e os eventos são retornados através de um canal de passagem de mensagens injetado na página.

---

## ⚙️ Referência de Configuração

### ⚙️ `HaxballConfig`

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `room_name` (alias `roomName`) | `str` | obrigatório | Nome visível da sala |
| `player_name` (alias `playerName`) | `str \| None` | `None` | Nome do bot (auto se `no_player=False`) |
| `password` | `str \| None` | `None` | Senha da sala |
| `max_players` (alias `maxPlayers`) | `int` | `16` | Máximo de jogadores (1–50) |
| `public` | `bool` | `True` | Mostrar sala no lobby |
| `no_player` (alias `noPlayer`) | `bool` | `True` | Host não entra como jogador |
| `token` | `str` | obrigatório (solicitado) | Token de autenticação HaxBall |
| `geo` | `GeoConfig \| None` | `None` | Geolocalização personalizada |
| `proxy_server` | `str \| None` | `None` | Proxy HTTP para o navegador |
| `headless` | `bool` | `True` | Executar navegador headless |
| `browser_executable_path` | `str \| None` | `None` | Caminho personalizado do Chromium |
| `browser_channel` | `str \| None` | `None` | Canal do navegador (ex. `"chrome"`) |
| `browser_args` | `list[str]` | `[]` | Argumentos extras do Chromium |
| `timeout_ms` | `int` | `30000` | Timeout do navegador |
| `headless_host_url` | `str` | `https://html5.haxball.com/headless` | URL do host headless |

---

## 🛠️ API da Sala

### 📡 Métodos

| Python | JS | Descrição |
|---|---|---|
| `send_chat(message, target_id?)` | `sendChat` | Enviar mensagem de chat |
| `set_player_admin(id, admin)` | `setPlayerAdmin` | Dar/revogar admin |
| `set_player_team(id, team)` | `setPlayerTeam` | Mudar time (0=spec, 1=red, 2=blue) |
| `kick_player(id, reason?, ban?)` | `kickPlayer` | Expulsar ou banir |
| `clear_ban(id)` | `clearBan` | Limpar ban |
| `clear_bans()` | `clearBans` | Limpar todos os bans |
| `set_score_limit(limit)` | `setScoreLimit` | Gols para vencer |
| `set_time_limit(minutes)` | `setTimeLimit` | Limite de tempo |
| `set_default_stadium(name)` | `setDefaultStadium` | Estádio por nome |
| `set_custom_stadium(contents)` | `setCustomStadium` | Estádio personalizado (HBS) |
| `set_teams_lock(locked)` | `setTeamsLock` | Bloquear times |
| `set_team_colors(team, angle, text, colors)` | `setTeamColors` | Cores do time |
| `start_game()` | `startGame` | Iniciar partida |
| `stop_game()` | `stopGame` | Parar partida |
| `pause_game(state)` | `pauseGame` | Pausar/retomar |
| `get_player(id)` → `Player \| None` | `getPlayer` | Informação do jogador |
| `get_player_list()` → `list[Player]` | `getPlayerList` | Todos os jogadores |
| `get_scores()` → `Scores \| None` | `getScores` | Placar |
| `set_password(password)` | `setPassword` | Senha da sala |
| `set_require_recaptcha(required)` | `setRequireRecaptcha` | Ativar/desativar recaptcha |
| `reorder_players(ids)` | `reorderPlayers` | Reordenar lista |
| `send_announcement(msg, color?, style?)` | `sendAnnouncement` | Anúncio colorido |
| `set_kick_rate_limit(min, rate, burst, by?)` | `setKickRateLimit` | Limite de expulsões |
| `set_player_avatar(id, avatar)` | `setPlayerAvatar` | Avatar do jogador |
| `set_disc_properties(id, props)` | `setDiscProperties` | Física do disco |
| `get_disc_properties(id)` → `DiscProperties` | `getDiscProperties` | Física do disco |
| `set_player_disc_properties(id, props)` | `setPlayerDiscProperties` | Física do disco do jogador |
| `get_player_disc_properties(id)` → `DiscProperties` | `getPlayerDiscProperties` | Física do disco do jogador |
| `get_disc_count()` → `int` | `getDiscCount` | Total de discos |
| `wait_for_room_link(timeout?)` → `str` | — | Aguarda até obter o link |

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

## 📄 Licença

Este projeto é um wrapper em torno da API oficial do HaxBall Headless Host. Não é afiliado nem endossado pelo HaxBall.

© 2026 contribuidores do haxball.py

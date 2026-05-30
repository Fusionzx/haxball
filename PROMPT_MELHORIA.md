# 🚀 PROMPT DE MELHORIA ULTRA PERFORMÁTICA — haxball-py + haxball-extended-room

## Contexto

Temos um projeto chamado **haxball-py** (Python) que faz uma ponte com a API Headless do HaxBall via Playwright (Chromium). O código atual tem:

- `haxball_py/` — pacote principal
  - `browser.py` — Bridge Playwright + JS injection
  - `room.py` — Classe `Room` que espelha o `RoomObject` nativo
  - `client.py` — `HaxballClient` (gerencia ciclo de vida do browser)
  - `config.py` — `HaxballConfig` (validação com Pydantic)
  - `models.py` — `Player`, `Scores`, `DiscProperties`, `Position`
  - `events.py` — `EventEmitter` simples
  - `errors.py` — Exceções customizadas
- `pyproject.toml` — dependências: playwright, pydantic
- `examples/basic_room.py`

Do outro lado, existe a biblioteca **haxball-extended-room** (JavaScript/TypeScript) que é um superconjunto da API oficial do HaxBall. Ela adiciona:

- **Comandos** com sistema de permissão (roles), aliases, descrição, remoção automática da mensagem
- **Player extendido** — herdando de AbstractDisc, com `.admin`, `.radius`, `.kick()`, `.ban()`, `.ip`, `.conn`, `.reply()`, `.setAvatar()`, `.addRole()`, `.hasRole()`, `.removeRole()`, `.settings`, `.team()`, `.position()`, `.tag()`, `.mention()`
- **Disc completo** — `.x`, `.y`, `.xspeed`, `.yspeed`, `.xgravity`, `.ygravity`, `.radius`, `.bCoeff`, `.invMass`, `.damping`, `.cMask`, `.cGroup`, `.color`, `.distanceTo()`, `.collidingWith()`, `.settings`
- **Módulos** — classes com decoradores `@Module`, `@ModuleCommand`, `@Event`, `@CustomEvent`
- **PlayerList** — classe especial com `.size`, `.add()`, `.remove()`, `.get()`, `.getAll()`, `.values()`, `.order()`, `.first()`, `.last()`, `.getByName()`, `.getByAuth()`, `.getByConnOrIP()`, `.kick()`, `.ban()`, `.spectators()`, `.red()`, `.blue()`, `.teams()`, `.admins()`, `.reply()`, `.toString()`
- **Room expandido** — `.state`, `.customEvents` (EventEmitter Node.js-style), `.logging`, `.noPermissionMessage`, `.players` (PlayerList), `.discs`, `.scores`, `.ball`, `.discCount`, `.commands`, `.password`, `.prefix`, `.modules`, `.native`, `.paused`, `.command()`, `.removeCommand()`, `.module()`, `.removeModule()`, `.chat()` (deprecated), `.send()` (MessageObject), `.reorderPlayers()` com `moveToTop`, `.setStadium()` (aceita JSON ou nome), `.lockTeams()`, `.unlockTeams()`, `.enableCaptcha()`, `.disableCaptcha()`, `.startRecording()`, `.stopRecording()`
- **Command** — `.name`, `.aliases`, `.roles`, `.desc`, `.usage`, `.deleteMessage`, `.func`, `.isAllowed()`, `.run()`
- **CommandExecInfo** — `.player`, `.message`, `.room`, `.at`, `.arguments[]`
- **CommandArgument** — `.number`, `.yesno`, `.password`, `.extended`, `.specialExtended`, `.toNumber()`, `.toString()`
- **MessageObject** — `message`, `targetID?`, `color?`, `style?`, `sound?`
- **Enums globais** — `Teams` (Red=1, Blue=2, Spectators=0), `Stadiums`, `ChatSounds`, `ChatStyle` (normal, bold, italic, small, small-bold, small-italic), `Colors` (centenas de cores nomeadas)
- **Settings** — `[setting: string]: any` (compartilhado entre módulos via `room.state`)
- **TeamColors** — `angle`, `textColor`, `colors[]`
- **Sistema de tradução** — `Translator` function + `languagePack` nos módulos

## O que precisa ser feito

**O objetivo é FUNDIR tudo isso no haxball-py**, criando uma camada "Extended" em Python que seja ultra performática, idiomática (Python 3.10+), totalmente tipada, e que mantenha compatibilidade com a API nativa.

### Requisitos específicos

#### 1. REFATORAÇÃO DA ARQUITETURA

Reorganizar `haxball_py/` nesta estrutura:

```
haxball_py/
  __init__.py          # Re-exporta tudo
  _bridge.py           # Bridge Playwright (atual browser.py)
  _native.py           # Binding direto para o RoomObject JS (baixo nível)
  room.py              # Room NATIVO (como está, mas limpo)
  extended.py          # --- NOVO: RoomExtended que EMPACOTA Room nativo ---
  player.py            # PlayerExtended com disc properties, roles, kick, ban, reply
  player_list.py       # PlayerList completo
  disc.py              # Disc + AbstractDisc
  command.py           # Command, CommandExecInfo, CommandArgument
  module.py            # Module base, decorators, ModuleOptions
  event_emitter.py     # EventEmitter melhorado (com tradução de nomes JS<->Python)
  enums.py             # Teams, Stadiums, ChatSounds, ChatStyle, Colors
  models.py            # Modelos Pydantic (Position, Scores, DiscProperties, etc.)
  config.py            # HaxballConfig
  errors.py            # Exceções
  utils.py             # Conversores, helpers de cor, validação
```

#### 2. PRINCÍPIOS DE PERFORMANCE

- **Zero overhead em hot paths**: `onGameTick` (60fps) não pode criar objetos desnecessários
- **Lazy conversion**: só converter payloads JS para Python quando tiver handler registrado
- **Pooling de objetos**: reutilizar instâncias de `Player` quando possível, em vez de recriar
- **Caching de propriedades**: `room.players` não deve chamar JS toda vez — usar cache síncrono atualizado pelos eventos
- **Minimizar idas ao browser**: operações batch quando possível
- **Evitar Pydantic em runtime no hot path**: usar Pydantic só para validação na criação; em callbacks frequentes, usar `__slots__` ou dataclasses simples
- **Type hints completos** para que meupy/Pyright possa otimizar
- **Protocols/ABCs** em vez de duck typing — permitir checagem estática

#### 3. PLAYER EXTENDED

```python
class AbstractDisc:
    x: float | None
    y: float | None
    xspeed: float | None
    yspeed: float | None
    xgravity: float | None
    ygravity: float | None
    radius: float | None
    b_coeff: float | None
    inv_mass: float | None
    damping: float | None
    c_mask: int | None
    c_group: int | None
    color: int | None  # -1 = transparente
    settings: dict[str, Any]
    
    def distance_to(self, other: AbstractDisc) -> float | None
    def colliding_with(self, other: AbstractDisc) -> bool

class Player(AbstractDisc):
    id: int
    name: str
    auth: str | None
    conn: str | None
    ip: str | None  # decodificado do conn
    admin: bool
    team: int
    position: Position | None
    roles: list[Role]
    settings: dict[str, Any]
    _room_ref: RoomExtended  # referência fraca para o room
    
    def kick(self, reason: str = "") -> None
    def ban(self, reason: str = "") -> None
    def reply(self, message: str, color: int | None = None, style: str | None = None) -> None
    def set_avatar(self, avatar: str) -> None
    def clear_avatar(self) -> None
    def add_role(self, role: Role) -> None
    def remove_role(self, role: Role) -> None
    def has_role(self, role: Role) -> bool
    def tag(self) -> str  # "name #id"
    def mention(self) -> str  # "@player"
    def can_kick(self, disc: AbstractDisc) -> bool
```

#### 4. COMMAND SYSTEM

```python
@dataclass
class CommandArgument:
    raw: str
    number: bool    # /^\d+$/
    yesno: bool     # /^(y(es)?|n(o)?)/i
    password: bool  # senha válida
    extended: bool  # alfanumérico extendido
    special_extended: bool
    
    def to_number(self) -> int
    def to_string(self) -> str

@dataclass
class CommandExecInfo:
    player: Player
    message: str
    room: RoomExtended
    at: datetime
    arguments: list[CommandArgument]

class Command:
    name: str
    aliases: list[str]
    roles: list[Role | str]
    desc: str
    usage: str
    delete_message: bool
    func: Callable[[CommandExecInfo], Awaitable[None] | None]
    
    def is_allowed(self, player: Player) -> bool
    async def run(self, info: CommandExecInfo) -> None
```

#### 5. SISTEMA DE MÓDULOS

```python
class ModuleMeta(type):
    # metaclass que processa decoradores

class Module(metaclass=ModuleMeta):
    room: RoomExtended
    settings: dict[str, Any]
    translate: TranslatorFunc
    
    # Events e Commands são descobertos por reflection
    # e registrados automaticamente no room quando módulo é carregado

# Decoradores
def module(cls) -> type[Module]
def module_command(options: CommandOptions | None = None) -> Callable
def event(fn: Callable) -> Callable
def custom_event(fn: Callable) -> Callable

# Exemplo de uso:
@module
class AFKModule(Module):
    @module_command(usage="afk")
    async def afk(self, info: CommandExecInfo) -> None:
        if info.player.settings.get("afk"):
            info.player.settings["afk"] = False
            self.room.send(f"{info.player.name} não está mais AFK!")
        else:
            info.player.settings["afk"] = True
            self.room.send(f"{info.player.name} está AFK!")
    
    @event
    async def on_player_team_change(self, player: Player) -> None:
        if player.settings.get("afk") and player.team != Teams.SPECTATORS:
            player.team = Teams.SPECTATORS
```

#### 6. PLAYERLIST

```python
class PlayerList(collections.abc.MutableMapping):
    size: int
    _players: dict[int, Player]
    
    def add(self, player: Player) -> None
    def remove(self, player: Player | int) -> None
    def get(self, predicate: int | Callable[[Player], bool]) -> Player | None
    def get_all(self, predicate: Callable[[Player], bool]) -> PlayerList
    def values(self) -> list[Player]
    def order(self, room: RoomExtended) -> PlayerList
    def first(self) -> Player | None
    def last(self) -> Player | None
    def get_by_name(self, name: str) -> PlayerList
    def get_by_auth(self, auth: str) -> Player | None
    def get_by_conn_or_ip(self, conn_or_ip: str) -> PlayerList
    def kick(self, reason: str = "") -> None
    def ban(self, reason: str = "") -> None
    def spectators(self) -> PlayerList
    def red(self) -> PlayerList
    def blue(self) -> PlayerList
    def teams(self) -> PlayerList
    def admins(self) -> PlayerList
    def reply(self, message: str, color: int | None = None, style: str | None = None) -> None
    def __str__(self) -> str
```

#### 7. ROOM EXTENDED (empacota Room nativo)

```python
class RoomExtended:
    # Propriedades
    name: str
    player_name: str | None
    max_players: int
    geo: GeoConfig | None
    token: str | None
    no_player: bool
    state: dict[str, Any]  # estado compartilhado entre módulos
    custom_events: EventEmitter
    logging: bool
    players: PlayerList  # cache síncrono!
    discs: list[Disc]
    scores: Scores | None
    ball: Disc | None
    disc_count: int | None
    commands: list[Command]
    password: str | None
    prefix: str  # "!" por padrão
    modules: dict[str, Module]
    paused: bool
    
    # Referência ao nativo
    native: Room  # o Room original (para baixo nível)
    
    # Métodos extendidos
    def command(self, options: CommandOptions) -> None
    def remove_command(self, name: str) -> None
    def module(self, mod_cls: type[Module], options: ModuleOptions | None = None) -> RoomExtended
    def remove_module(self, module_or_name: str | type[Module]) -> None
    def send(self, message: str, color: int | None = None, style: str | None = None, target_id: int | None = None, sound: int | None = None) -> None
    def set_stadium(self, stadium: str | dict) -> None  # aceita nome OU HBS JSON
    def lock_teams(self) -> None
    def unlock_teams(self) -> None
    def enable_captcha(self) -> None
    def disable_captcha(self) -> None
    def start_recording(self) -> None
    def stop_recording(self) -> bytes | None
    def is_game_in_progress(self) -> bool
    def set_no_permission_message(self, message: str, color: int | None = None) -> None
    
    # Eventos (setter-only, igual Room nativo)
    on_player_join: Callable[[Player], Awaitable[None] | None] | None
    on_player_leave: Callable[[Player], Awaitable[None] | None] | None
    ...
```

#### 8. ENUMS E CONSTANTES

```python
from enum import IntEnum

class Teams(IntEnum):
    SPECTATORS = 0
    RED = 1
    BLUE = 2

class ChatStyle:
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    SMALL = "small"
    SMALL_BOLD = "small-bold"
    SMALL_ITALIC = "small-italic"

class ChatSounds:
    NONE = 0
    NORMAL = 1
    NOTIFICATION = 2

# Stadiums como string constants
class Stadiums:
    CLASSIC = "Classic"
    BIG = "Big"
    SMALL = "Small"
    ROUND = "Round"
    BIG_BEACH = "BigBeach"
    SMALL_BEACH = "SmallBeach"
    ...

# Colors — centenas de cores como ints hex
class Colors:
    WHITE = 0xFFFFFF
    BLACK = 0x000000
    RED = 0xFF0000
    GREEN = 0x00FF00
    BLUE = 0x0000FF
    MEDIUM_SEA_GREEN = 0x3CB371
    ...
```

#### 9. MELHORIAS NO BRIDGE (browser.py → _bridge.py)

- **Adicionar suporte a `proxy_server` funcional** (já tem no config mas precisa testar)
- **Injeção do JS do extended room** — além do BRIDGE_JS atual, injetar também a lógica do haxball-extended-room no browser para que métodos como `setPlayerDiscProperties`, `startRecording`, `stopRecording`, `setRequireRecaptcha` funcionem (alguns já estão, outros não)
- **Tratamento de erros mais robusto** — reconexão automática se o browser cair
- **Timeout configurável por operação**
- **Logging do tráfego JS<->Python** (modo debug)

#### 10. BACKWARDS COMPATIBILITY

- `Room` original (nativo) deve continuar funcionando exatamente como está
- `RoomExtended` deve ser uma CAMADA acima, que recebe um `Room` nativo no construtor
- Usuário pode escolher qual usar:

```python
# Modo simples (atual)
from haxball_py import HaxballClient, HaxballConfig
client = HaxballClient()
room = await client.init(config)
room.on_player_join = lambda p: print(p.name)

# Modo extended (novo)
from haxball_py.extended import HaxballClientExtended
client = HaxballClientExtended()
room = await client.init(config)  # retorna RoomExtended
room.command(name="kick", roles=["admin"], func=lambda info: ...)
```

#### 11. TESTES

- Testes unitários para `PlayerList`, `Command`, `CommandArgument`, `CommandExecInfo`
- Testes para o sistema de módulos (decorators, carregamento, eventos)
- Testes de integração (browser real opcional, pelo menos mock do bridge)
- Usar `pytest` + `pytest-asyncio`

#### 12. DOCUMENTAÇÃO (docstrings)

- Documentar todas as classes e métodos públicos
- Exemplos de uso em docstrings (formato Google ou NumPy)
- Atualizar `README.md` com exemplos do Extended Room

---

## OBSERVAÇÕES FINAIS

- **Performance é prioridade absoluta** — evitar alocações desnecessárias, usar `__slots__`, lazy evaluation, caching
- **Código limpo e Pythonico** — seguir PEP 8, PEP 484 (type hints), PEP 557 (dataclasses)
- **Não quebrar a API existente** — o `Room` nativo deve continuar intacto
- **Seguir o design do HER original** — a ideia é portar os conceitos, não copiar cegamente o JS
- **Usar asyncio corretamente** — todas as chamadas ao browser são async; eventos podem ser sync ou async
- **Tratar erros graciosamente** — não deixar o bot quebrar por causa de um evento mal formatado
- **IO-bound tasks devem usar asyncio** — não bloquear o event loop

---

**Mão na massa!** 🐍⚡

Quero ver:
1. Estrutura de diretórios reorganizada
2. Código de cada módulo completo (não esqueleto — implementação real)
3. Testes funcionando
4. Exemplo funcional do `basic_room.py` usando `RoomExtended`
5. OBS: Não apague ou modifique `room.py`, `client.py`, `browser.py`, `events.py`, `config.py`, `models.py`, `errors.py` originais — crie arquivos NOVOS. Os antigos ficam para compatibilidade.

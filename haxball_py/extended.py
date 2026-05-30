from __future__ import annotations
import asyncio
import inspect
import sys
from datetime import datetime
from typing import Any, Awaitable, Callable, Type
from .room import Room
from ._bridge import ExtendedBrowserBridge
from .client import HaxballClient
from .config import HaxballConfig
from .event_emitter import EventEmitter
from .player import Player
from .player_list import PlayerList
from .command import Command, CommandArgument, CommandExecInfo
from .module import Module
from .disc import Disc
from .logger import RoomLogger
from .models import Scores, Position, Player as NativePlayer
from .enums import Teams


class RoomExtended:
    """The main high-level API for controlling a HaxBall room.

    ``RoomExtended`` wraps a :class:`~haxball_py.room.Room` (bridge) or
    :class:`~haxball_py.room_native.RoomNative` (native engine) and adds:

    * **Live player properties** — ``player.admin = True``, ``player.team = Teams.Red``
    * **Module system** — organise your code into reusable :class:`Module` classes
    * **Command system** — auto-parsed chat commands with permission roles
    * **Built-in logging** — timestamped event output via :class:`RoomLogger`
    * **Chainable player filters** — ``room.players.admins().red()``
    * **Convenience methods** — ``room.start()``, ``room.pause()``, ``room.send()``, etc.

    Usage::

        room = await client.init(config)
        room.module(MyModule)

        room.send("Hello everyone!", color=0xFFFF00)
        room.set_stadium("Big")
        room.start()
        print(f"Link: {room.room_link}")
    """

    def __init__(self, native_room: Room, config: HaxballConfig) -> None:
        self.native = native_room
        """The underlying native :class:`~haxball_py.room.Room` or
        :class:`~haxball_py.room_native.RoomNative` instance.  Use this to
        access low-level methods such as ``room.native.set_score_limit()``."""

        self.name: str = config.room_name
        """The room's display name, set at creation time."""

        self.player_name: str | None = config.player_name
        """The bot player's name, or ``None`` if ``no_player`` was ``True``."""

        self.max_players: int = config.max_players
        """The maximum number of players the room accepts."""

        self.geo = config.geo
        """The geographic location hint (:class:`~haxball_py.config.GeoConfig`), or ``None``."""

        self.token: str | None = config.token
        """The HaxBall authentication token used to create the room, or ``None``."""

        self.no_player: bool = config.no_player
        """Whether the room has no visible bot player."""

        self.state: dict[str, Any] = {}
        """Shared mutable state accessible by all modules.

        Useful for cross-module communication::

            room.state.chat_muted = True
        """

        self.custom_events = EventEmitter()
        """An :class:`~haxball_py.event_emitter.EventEmitter` for defining and
        emitting custom events.  Subscribe with ``on()``, fire with ``emit()``.
        """

        self.logging: bool = True
        """Whether to automatically print timestamped event logs to stdout.

        Example::

            14:30:15  Fusion2 has joined
            14:30:20  Fusion2 has left
        """

        self.players = PlayerList()
        """The :class:`~haxball_py.player_list.PlayerList` of currently
        connected players.  Access by ID: ``room.players[1]``."""

        self.commands: list[Command] = []
        """All registered :class:`~haxball_py.command.Command` objects."""

        self.password: str | None = config.password
        """The current room password, or ``None``."""

        self.prefix: str = config.prefix
        """The command prefix (default ``"!"``).  Set via
        :attr:`HaxballConfig.prefix` or changed at runtime before modules
        register commands::

            room.prefix = "/"
        """

        self.modules: dict[str, Module] = {}
        """Loaded modules keyed by class name."""

        self.paused: bool = False
        """Whether the game is currently paused."""

        self._no_permission_message: str | None = None
        self._logger = RoomLogger()
        self._no_permission_color: int | None = None

        # Intercept event handling
        bridge = getattr(self.native, "_bridge", None)
        if bridge is not None:
            bridge.set_emit_callback(self._handle_extended_js_event)
        else:
            engine = getattr(self.native, "_engine", None)
            if engine is not None:
                for name in self.native._EVENTS.values():
                    engine._callbacks[name] = lambda *args, n=name: self._handle_extended_js_event(
                        n, list(args)
                    )

    @property
    def room_link(self) -> str | None:
        """The room's shareable URL, or ``None`` before it is available."""
        return self.native.room_link

    @property
    def discs(self) -> list[Disc]:
        """A list of all active player discs currently on the field."""
        discs_list = []
        for p in self.players.values():
            if p.position:
                discs_list.append(p)
        return discs_list

    async def get_scores(self) -> Scores | None:
        """Fetches the current game scores.

        :returns: A :class:`~haxball_py.models.Scores` object, or ``None``
                  if no game is in progress.
        """
        return await self.native.get_scores()

    @property
    def disc_count(self) -> int:
        """The number of active discs on the field (players + ball + stadium)."""
        return len(self.discs)

    def set_no_permission_message(self, message: str, color: int | None = None) -> None:
        """Sets a message shown to players who try to run a command they are
        not allowed to execute.

        :param message: The message text.
        :param color: An optional RGB integer (e.g. ``0xFF0000`` for red).
        """
        self._no_permission_message = message
        self._no_permission_color = color

    def command(
        self,
        name: str,
        func: Callable[[CommandExecInfo], Awaitable[None] | None],
        aliases: list[str] | None = None,
        roles: list[Any] | None = None,
        desc: str = "",
        usage: str = "",
        delete_message: bool = True,
    ) -> None:
        """Registers a chat command.

        :param name: The command name (e.g. ``"kick"``).
        :param func: The handler function receiving a :class:`CommandExecInfo`.
        :param aliases: Alternative names (e.g. ``["ban", "disconnect"]``).
        :param roles: Required permission roles (empty = anyone).
        :param desc: Short description for help commands.
        :param usage: Usage string (e.g. ``"kick #id reason"``).
        :param delete_message: Whether to hide the player's original message.
        """
        cmd = Command(
            name=name,
            func=func,
            aliases=aliases or [],
            roles=roles or [],
            desc=desc,
            usage=usage,
            delete_message=delete_message,
        )
        self.commands.append(cmd)
        self._sync_bare_commands()

    def remove_command(self, name: str) -> None:
        """Unregisters a command by name or alias."""
        self.commands = [
            cmd for cmd in self.commands if cmd.name != name and name not in cmd.aliases
        ]
        self._sync_bare_commands()

    def _bare_command_names(self) -> set[str]:
        names: set[str] = set()
        for cmd in self.commands:
            for name in [cmd.name, *cmd.aliases]:
                if len(name) == 1:
                    names.add(name.lower())
        return names

    def _sync_bare_commands(self) -> None:
        engine = getattr(self.native, "_engine", None)
        if engine is None:
            return
        try:
            asyncio.create_task(engine.set_bare_command_names(sorted(self._bare_command_names())))
        except RuntimeError:
            pass

    def module(self, mod_cls: Type[Module], options: dict[str, Any] | None = None) -> RoomExtended:
        """Loads and registers a :class:`Module`.

        Scans the module class for ``@event``, ``@module_command`` and
        ``@custom_event`` decorators and wires them up automatically.

        :param mod_cls: The module class (decorated with ``@module``).
        :param options: Optional settings dict passed to the module's constructor.
        :returns: ``self`` for chaining.
        """
        mod_name = mod_cls.__name__
        if mod_name in self.modules:
            return self

        mod_instance = mod_cls(self, options)
        self.modules[mod_name] = mod_instance

        # Register command methods
        for key, cmd_opts in mod_cls._commands:
            method = getattr(mod_instance, key)
            self.command(
                name=cmd_opts["name"],
                func=method,
                aliases=cmd_opts["aliases"],
                roles=cmd_opts["roles"],
                desc=cmd_opts["desc"],
                usage=cmd_opts["usage"],
                delete_message=cmd_opts["delete_message"],
            )

        # Register event methods
        for key, event_name in mod_cls._events:
            method = getattr(mod_instance, key)
            self.custom_events.on(event_name, method)

        # Register custom events
        for key, custom_name in mod_cls._custom_events:
            method = getattr(mod_instance, key)
            self.custom_events.on(custom_name, method)

        return self

    def remove_module(self, module_or_name: str | Type[Module]) -> None:
        """Unloads a previously loaded module.

        :param module_or_name: The module class or its string name.
        """
        mod_name = module_or_name if isinstance(module_or_name, str) else module_or_name.__name__
        if mod_name not in self.modules:
            return

        mod_instance = self.modules.pop(mod_name)
        mod_cmds = [opts["name"] for _, opts in mod_instance.__class__._commands]
        self.commands = [cmd for cmd in self.commands if cmd.name not in mod_cmds]

        for _, event_name in mod_instance.__class__._events:
            pass
        for _, custom_name in mod_instance.__class__._custom_events:
            pass

    async def send(
        self,
        message: str,
        color: int | None = None,
        style: str | None = None,
        target_id: int | None = None,
        sound: int | None = None,
    ) -> None:
        """Sends an in-game message.

        :param message: The text to send.
        :param color: RGB integer color (e.g. ``0x00FFFF`` for cyan).
        :param style: Text style (``"normal"``, ``"bold"``, ``"italic"``,
                      ``"small"``, ``"small-bold"``, ``"small-italic"``).
        :param target_id: If set, sends a **private message** to that player.
        :param sound: Sound effect (0 = none, 1 = normal, 2 = notification).
        """
        target_name = None
        if target_id is not None:
            p = self.players.get(target_id)
            target_name = p.name if p else f"#{target_id}"
        tag = f"[PRIVATE -> {target_name}]" if target_name else "[BROADCAST]"
        print(f"{datetime.now().strftime('%H:%M:%S')} {tag} {message}", flush=True)
        try:
            await self.native.send_announcement(message, target_id, color, style, sound)
        except Exception as e:
            print(f"[send] Failed to send message: {e}", file=sys.stderr, flush=True)

    def set_stadium(self, stadium: str | dict) -> None:
        """Changes the stadium.

        :param stadium: A stadium name (``"Big"``, ``"Classic"``, ``"Hockey"``)
                        or a stadium JSON dict.
        """
        if isinstance(stadium, dict):
            import json

            asyncio.create_task(self.native.set_custom_stadium(json.dumps(stadium)))
        else:
            if stadium.strip().startswith("{"):
                asyncio.create_task(self.native.set_custom_stadium(stadium))
            else:
                asyncio.create_task(self.native.set_default_stadium(stadium))

    def lock_teams(self) -> None:
        """Locks team switching — players cannot change teams on their own."""
        asyncio.create_task(self.native.set_teams_lock(True))

    def unlock_teams(self) -> None:
        """Unlocks team switching."""
        asyncio.create_task(self.native.set_teams_lock(False))

    def enable_captcha(self) -> None:
        """Requires a CAPTCHA from every player before they join."""
        asyncio.create_task(self.native.set_require_recaptcha(True))

    def disable_captcha(self) -> None:
        """Disables the CAPTCHA requirement."""
        asyncio.create_task(self.native.set_require_recaptcha(False))

    def start_recording(self) -> None:
        """Begins recording a HaxBall replay.

        Call :meth:`stop_recording` to finish — the replay data is returned
        as ``bytes``.
        """
        asyncio.create_task(self.native.call("startRecording"))

    async def stop_recording(self) -> bytes | None:
        """Stops recording and returns the replay data.

        :returns: The replay as a ``bytes`` object.

        .. warning::
           This method is only available when using the **bridge** backend.
           The native engine does not support binary replay output.
        """
        bridge = self.native._bridge
        if isinstance(bridge, ExtendedBrowserBridge):
            return await bridge.call_binary("stopRecording")
        return await bridge.call("stopRecording")

    async def is_game_in_progress(self) -> bool:
        """Checks whether a game is currently running.

        :returns: ``True`` if a game is active.
        """
        scores = await self.get_scores()
        return scores is not None

    @property
    async def scores(self) -> Scores | None:
        """The current :class:`~haxball_py.models.Scores`, or ``None``."""
        return await self.native.get_scores()

    @property
    async def ball(self) -> Disc | None:
        """The ball disc (index 0), or ``None`` if no game is in progress."""
        count = await self.native.get_disc_count()
        if count is None or count == 0:
            return None
        props = await self.native.get_disc_properties(0)
        if props is None:
            return None
        return Disc(
            index=0,
            room=self,
            x=props.x,
            y=props.y,
            xspeed=props.xspeed,
            yspeed=props.yspeed,
            radius=props.radius,
            b_coeff=props.bCoef,
            inv_mass=props.invMass,
            damping=props.damping,
            c_mask=props.cMask,
            c_group=props.cGroup,
            color=props.color,
        )

    @property
    def password(self) -> str | None:
        """The room password, or ``None``.

        Setting this property locks/unlocks the room::

            room.password = "secret123"
            room.password = None  # remove password
        """
        return self._password if hasattr(self, "_password") else None

    @password.setter
    def password(self, value: str | None) -> None:
        self._password = value
        if value is None:
            asyncio.create_task(self.native.set_password(None))
        else:
            asyncio.create_task(self.native.set_password(value))

    def clear_password(self) -> None:
        """Removes the room password."""
        self._password = None
        asyncio.create_task(self.native.set_password(None))

    def unban(self, player_id: int) -> None:
        """Unbans a previously banned player by their old player ID."""
        asyncio.create_task(self.native.clear_ban(player_id))

    def unban_all(self) -> None:
        """Clears all bans."""
        asyncio.create_task(self.native.clear_bans())

    def start(self) -> None:
        """Starts the game if none is in progress."""
        asyncio.create_task(self.native.start_game())

    def stop(self) -> None:
        """Stops the current game if one is in progress."""
        asyncio.create_task(self.native.stop_game())

    def pause(self) -> None:
        """Pauses the game."""
        asyncio.create_task(self.native.pause_game(True))

    def unpause(self) -> None:
        """Unpauses the game."""
        asyncio.create_task(self.native.pause_game(False))

    async def _handle_extended_js_event(self, event_name: str, args: list[Any]) -> None:
        # 1. Sync local cache first
        player_obj = None
        if event_name == "onPlayerJoin" and args:
            raw_player = args[0]
            player_obj = Player(
                id=raw_player["id"],
                name=raw_player["name"],
                team=raw_player["team"],
                admin=raw_player.get("admin", False),
                auth=raw_player.get("auth"),
                conn=raw_player.get("conn"),
                position=Position.model_validate(raw_player["position"])
                if raw_player.get("position")
                else None,
                room=self,
            )
            self.players.add(player_obj)

        elif event_name == "onPlayerLeave" and args:
            raw_player = args[0]
            player_obj = self.players.get(raw_player["id"])
            if player_obj:
                self.players.remove(player_obj)

        elif event_name == "onPlayerAdminChange" and args:
            raw_player = args[0]
            player_obj = self.players.get(raw_player["id"])
            if player_obj:
                player_obj.admin = raw_player.get("admin", False)

        elif event_name == "onPlayerTeamChange" and args:
            raw_player = args[0]
            player_obj = self.players.get(raw_player["id"])
            if player_obj:
                player_obj.team = raw_player.get("team", Teams.SPECTATORS)

        elif event_name == "onPlayerActivity" and args:
            raw_player = args[0]
            player_obj = self.players.get(raw_player["id"])

        elif event_name == "onGamePause":
            self.paused = True

        elif event_name == "onGameUnpause":
            self.paused = False

        # 2. Check for Chat Command
        is_command = False
        if event_name == "onPlayerChat" and args:
            raw_player = args[0]
            message = args[1]
            player_obj = self.players.get(raw_player["id"])
            parts = []
            if message.startswith(self.prefix):
                parts = message[len(self.prefix) :].split(" ")
            elif isinstance(message, str):
                split_message = message.split(" ")
                if split_message and split_message[0].lower() in self._bare_command_names():
                    parts = split_message

            if player_obj and parts:
                is_command = True
                cmd_name = parts[0]
                cmd_args = parts[1:]

                # Look up command
                matched_cmd = None
                for cmd in self.commands:
                    if cmd.name == cmd_name or cmd_name in cmd.aliases:
                        matched_cmd = cmd
                        break

                if matched_cmd:
                    if matched_cmd.is_allowed(player_obj):
                        info = CommandExecInfo(
                            player=player_obj,
                            message=message,
                            room=self,
                            at=datetime.now(),
                            arguments=[CommandArgument(raw=arg) for arg in cmd_args],
                        )
                        asyncio.create_task(matched_cmd.run(info))
                    else:
                        if self._no_permission_message:
                            player_obj.reply(
                                self._no_permission_message, color=self._no_permission_color
                            )

        # 3. Call native room handlers if registered
        python_name = next((py for py, js in self.native._EVENTS.items() if js == event_name), None)
        if event_name == "onRoomLink" and args:
            object.__setattr__(self.native, "_room_link", args[0])

        # Execute custom event listeners registered on Module system
        converted_args = [self.native._convert_payload(arg) for arg in args]
        # Replace native Pydantic Player models with our extended Player objects
        for idx, val in enumerate(converted_args):
            if isinstance(val, NativePlayer):
                matched = self.players.get(val.id)
                if matched:
                    converted_args[idx] = matched

        # Don't log/emit prefixed commands (JS already suppressed from broadcast)
        if event_name == "onPlayerChat" and is_command:
            pass
        else:
            # Log event to console
            if self.logging and python_name:
                self._logger.log_event(python_name, *converted_args)

            # Trigger event emitter
            if python_name:
                asyncio.create_task(self.custom_events.emit(python_name, *converted_args))

        # Invoke native handlers
        native_handler = self.native._event_handlers.get(python_name) if python_name else None
        if native_handler:
            res = native_handler(*converted_args)
            if inspect.isawaitable(res):
                await res


class HaxballClientExtended(HaxballClient):
    """Extended client that creates a :class:`RoomExtended` with full
    module/command/logging support.

    :param backend: ``"native"`` to use Node.js directly, ``"auto"``
                    (default) to prefer native if Node.js is installed,
                    or ``"playwright"`` to use Playwright.
    """

    def __init__(self, backend: str = "auto") -> None:
        super().__init__()
        self.backend = backend
        self._engine: Any = None

    async def start(self, config: HaxballConfig) -> RoomExtended:
        """Creates and starts the room, returning a :class:`RoomExtended`.

        :param config: The :class:`~haxball_py.config.HaxballConfig` object.
        """
        # Determine backend to use
        use_native = False
        if self.backend == "native":
            use_native = True
        elif self.backend == "auto":
            try:
                import subprocess

                subprocess.run(
                    ["node", "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                use_native = True
            except Exception:
                use_native = False

        if use_native:
            from ._native_engine import NativeEngine
            from .room_native import RoomNative

            engine = NativeEngine(proxy=config.proxy_server, debug=config.debug)
            await engine.start()
            self._engine = engine
            native_room = RoomNative(engine)
            extended_room = RoomExtended(native_room, config)
            await engine.init_room(config.to_hbinit_config(), native_room._handle_js_event)
            self._room = extended_room
            return extended_room
        else:
            bridge = ExtendedBrowserBridge(
                headless=config.headless,
                proxy_server=config.proxy_server,
                browser_channel=config.browser_channel,
                browser_executable_path=config.browser_executable_path,
                browser_args=config.browser_args,
                timeout_ms=config.timeout_ms,
            )
            await bridge.start()
            await bridge.goto_headless_host(config.headless_host_url)

            native_room = Room(bridge)
            self._bridge = bridge

            extended_room = RoomExtended(native_room, config)
            await bridge.create_room(config.to_hbinit_config())
            self._room = extended_room
            return extended_room

    async def init(self, config: HaxballConfig | dict[str, Any]) -> RoomExtended:
        """Initialises a room, prompting for a token if none is set
        and checking the ``HAXBALL_TOKEN`` environment variable.

        :param config: A :class:`~haxball_py.config.HaxballConfig` or dict.
        """
        if isinstance(config, dict):
            token = config.get("token")
            if not token or "YOUR_TOKEN" in str(token):
                import os

                token = os.environ.get("HAXBALL_TOKEN")
                if not token:
                    token = input("Please enter your HaxBall token: ").strip()
                config["token"] = token
            config = HaxballConfig.model_validate(config)
        elif isinstance(config, HaxballConfig):
            if not config.token or "YOUR_TOKEN" in config.token:
                import os

                token = os.environ.get("HAXBALL_TOKEN")
                if not token:
                    token = input("Please enter your HaxBall token: ").strip()
                config.token = token
        return await self.start(config)

    async def close(self) -> None:
        """Shuts down the room and releases all resources."""
        await super().close()
        if self._engine is not None:
            self._engine.close()
            self._engine = None

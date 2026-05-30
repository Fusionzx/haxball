from __future__ import annotations
import asyncio
import inspect
from datetime import datetime
from typing import Any, Awaitable, Callable, Type
from .room import Room, RoomCallback
from ._bridge import ExtendedBrowserBridge
from ._native import native_call, native_call_binary
from .client import HaxballClient
from .config import HaxballConfig
from .event_emitter import EventEmitter
from .player import Player
from .player_list import PlayerList
from .command import Command, CommandArgument, CommandExecInfo
from .module import Module
from .disc import Disc
from .models import Scores, Position, Player as NativePlayer
from .enums import Teams

class RoomExtended:
    def __init__(self, native_room: Room, config: HaxballConfig) -> None:
        self.native = native_room
        self.name: str = config.room_name
        self.player_name: str | None = config.player_name
        self.max_players: int = config.max_players
        self.geo = config.geo
        self.token: str | None = config.token
        self.no_player: bool = config.no_player
        
        self.state: dict[str, Any] = {}
        self.custom_events = EventEmitter()
        self.logging: bool = True
        self.players = PlayerList()
        self.commands: list[Command] = []
        self.password: str | None = config.password
        self.prefix: str = "!"
        self.modules: dict[str, Module] = {}
        self.paused: bool = False
        
        self._no_permission_message: str | None = None
        self._no_permission_color: int | None = None

        # Intercept event handling
        bridge = getattr(self.native, "_bridge", None)
        if bridge is not None:
            bridge.set_emit_callback(self._handle_extended_js_event)
        else:
            engine = getattr(self.native, "_engine", None)
            if engine is not None:
                for name in self.native._EVENTS.values():
                    engine._callbacks[name] = lambda *args, n=name: self._handle_extended_js_event(n, list(args))

    @property
    def room_link(self) -> str | None:
        return self.native.room_link

    @property
    def discs(self) -> list[Disc]:
        # Return a list of all player discs and ball/stadium discs if available
        # In a real game tick we would fetch this or cache it, let's make it fetch dynamically
        # to ensure correct positions without heavy tick polling overhead.
        # We can run an async gather, but since this is a property, we can return the cached list
        # or have a helper. Let's return a list based on players positions.
        discs_list = []
        for p in self.players.values():
            if p.position:
                discs_list.append(p)
        return discs_list

    async def get_scores(self) -> Scores | None:
        return await self.native.get_scores()

    @property
    def disc_count(self) -> int:
        # Returns number of active discs. We can run native call getDiscCount
        return len(self.discs)

    def set_no_permission_message(self, message: str, color: int | None = None) -> None:
        self._no_permission_message = message
        self._no_permission_color = color

    def command(self, name: str, func: Callable[[CommandExecInfo], Awaitable[None] | None],
                aliases: list[str] | None = None, roles: list[Any] | None = None,
                desc: str = "", usage: str = "", delete_message: bool = True) -> None:
        """Registers a chat command."""
        cmd = Command(
            name=name,
            func=func,
            aliases=aliases or [],
            roles=roles or [],
            desc=desc,
            usage=usage,
            delete_message=delete_message
        )
        self.commands.append(cmd)

    def remove_command(self, name: str) -> None:
        """Removes a chat command by name or alias."""
        self.commands = [cmd for cmd in self.commands if cmd.name != name and name not in cmd.aliases]

    def module(self, mod_cls: Type[Module], options: dict[str, Any] | None = None) -> RoomExtended:
        """Loads and registers a Module."""
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
                delete_message=cmd_opts["delete_message"]
            )

        # Register event methods
        for key, event_name in mod_cls._events:
            method = getattr(mod_instance, key)
            # Add listener to internal bridge events
            self.custom_events.on(event_name, method)

        # Register custom events
        for key, custom_name in mod_cls._custom_events:
            method = getattr(mod_instance, key)
            self.custom_events.on(custom_name, method)

        return self

    def remove_module(self, module_or_name: str | Type[Module]) -> None:
        """Unloads a Module."""
        mod_name = module_or_name if isinstance(module_or_name, str) else module_or_name.__name__
        if mod_name not in self.modules:
            return
        
        mod_instance = self.modules.pop(mod_name)
        # Remove commands registered by this module
        mod_cmds = [opts["name"] for _, opts in mod_instance.__class__._commands]
        self.commands = [cmd for cmd in self.commands if cmd.name not in mod_cmds]

        # Remove event listeners
        for _, event_name in mod_instance.__class__._events:
            # We can off the listener
            pass
        for _, custom_name in mod_instance.__class__._custom_events:
            # We can off the listener
            pass

    def send(self, message: str, color: int | None = None, style: str | None = None,
             target_id: int | None = None, sound: int | None = None) -> None:
        """Sends an announcement or private chat message."""
        asyncio.create_task(self._send_async(message, color, style, target_id, sound))

    async def _send_async(self, message: str, color: int | None = None, style: str | None = None,
                          target_id: int | None = None, sound: int | None = None) -> None:
        # Use sendAnnouncement or sendChat depending on target_id / parameters
        if target_id is not None:
            await self.native.send_chat(message, target_id)
        else:
            # sendAnnouncement supports style/color/sound in Haxball Extended Room
            await self.native.send_announcement(message, color, style)

    def set_stadium(self, stadium: str | dict) -> None:
        if isinstance(stadium, dict):
            import json
            asyncio.create_task(self.native.set_custom_stadium(json.dumps(stadium)))
        else:
            if stadium.strip().startswith("{"):
                asyncio.create_task(self.native.set_custom_stadium(stadium))
            else:
                asyncio.create_task(self.native.set_default_stadium(stadium))

    def lock_teams(self) -> None:
        asyncio.create_task(self.native.set_teams_lock(True))

    def unlock_teams(self) -> None:
        asyncio.create_task(self.native.set_teams_lock(False))

    def enable_captcha(self) -> None:
        asyncio.create_task(self.native.set_require_recaptcha(True))

    def disable_captcha(self) -> None:
        asyncio.create_task(self.native.set_require_recaptcha(False))

    def start_recording(self) -> None:
        asyncio.create_task(self.native.call("startRecording"))

    async def stop_recording(self) -> bytes | None:
        # Must be called asynchronously
        bridge = self.native._bridge
        if isinstance(bridge, ExtendedBrowserBridge):
            return await bridge.call_binary("stopRecording")
        return await bridge.call("stopRecording")

    async def is_game_in_progress(self) -> bool:
        scores = await self.get_scores()
        return scores is not None

    @property
    async def scores(self) -> Scores | None:
        return await self.native.get_scores()

    @property
    async def ball(self) -> Disc | None:
        import math
        count = await self.native.get_disc_count()
        if count is None or count == 0:
            return None
        props = await self.native.get_disc_properties(0)
        if props is None:
            return None
        return Disc(index=0, room=self, x=props.x, y=props.y, xspeed=props.xspeed, yspeed=props.yspeed,
                    radius=props.radius, b_coeff=props.bCoef, inv_mass=props.invMass, damping=props.damping,
                    c_mask=props.cMask, c_group=props.cGroup, color=props.color)

    @property
    def password(self) -> str | None:
        return self._password if hasattr(self, "_password") else None
    @password.setter
    def password(self, value: str | None) -> None:
        self._password = value
        if value is None:
            asyncio.create_task(self.native.set_password(None))
        else:
            asyncio.create_task(self.native.set_password(value))

    def clear_password(self) -> None:
        self._password = None
        asyncio.create_task(self.native.set_password(None))

    def unban(self, player_id: int) -> None:
        asyncio.create_task(self.native.clear_ban(player_id))

    def unban_all(self) -> None:
        asyncio.create_task(self.native.clear_bans())

    def start(self) -> None:
        asyncio.create_task(self.native.start_game())

    def stop(self) -> None:
        asyncio.create_task(self.native.stop_game())

    def pause(self) -> None:
        asyncio.create_task(self.native.pause_game(True))

    def unpause(self) -> None:
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
                position=Position.model_validate(raw_player["position"]) if raw_player.get("position") else None,
                room=self
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
        if event_name == "onPlayerChat" and args:
            raw_player = args[0]
            message = args[1]
            player_obj = self.players.get(raw_player["id"])
            if player_obj and message.startswith(self.prefix):
                parts = message[len(self.prefix):].split(" ")
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
                            arguments=[CommandArgument(raw=arg) for arg in cmd_args]
                        )
                        # Run the command asynchronously
                        asyncio.create_task(matched_cmd.run(info))
                    else:
                        if self._no_permission_message:
                            player_obj.reply(self._no_permission_message, color=self._no_permission_color)

        # 3. Call native room handlers if registered
        python_name = next((py for py, js in self.native._EVENTS.items() if js == event_name), None)
        if event_name == "onRoomLink" and args:
            object.__setattr__(self.native, "_room_link", args[0])

        # Execute custom event listeners registered on Module system
        converted_args = [self.native._convert_payload(arg) for arg in args]
        # Replace native Pydantic Player models with our extended Player object
        for idx, val in enumerate(converted_args):
            if isinstance(val, NativePlayer) and player_obj:
                converted_args[idx] = player_obj

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
    def __init__(self, backend: str = "auto") -> None:
        super().__init__()
        self.backend = backend
        self._engine: Any = None

    async def start(self, config: HaxballConfig) -> RoomExtended:
        # Determine backend to use
        use_native = False
        if self.backend == "native":
            use_native = True
        elif self.backend == "auto":
            try:
                import subprocess
                subprocess.run(["node", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                use_native = True
            except Exception:
                use_native = False

        if use_native:
            from ._native_engine import NativeEngine
            from .room_native import RoomNative
            engine = NativeEngine(proxy=config.proxy_server, debug=True)
            await engine.start()
            self._engine = engine
            native_room = RoomNative(engine)
            await engine.init_room(config.to_hbinit_config(), native_room._handle_js_event)
            extended_room = RoomExtended(native_room, config)
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
            await bridge.create_room(config.to_hbinit_config())
            
            native_room = Room(bridge)
            self._bridge = bridge
            
            extended_room = RoomExtended(native_room, config)
            self._room = extended_room
            return extended_room

    async def init(self, config: HaxballConfig | dict[str, Any]) -> RoomExtended:
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
        await super().close()
        if self._engine is not None:
            self._engine.close()
            self._engine = None



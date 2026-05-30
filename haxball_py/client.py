from __future__ import annotations

from typing import Any

from .browser import BrowserBridge
from .config import HaxballConfig
from .room import Room


class HaxballClient:
    def __init__(self) -> None:
        self._bridge: BrowserBridge | None = None
        self._room: Room | None = None

    async def __aenter__(self) -> "HaxballClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    @property
    def room(self) -> Room:
        if self._room is None:
            raise RuntimeError("Room not initialized")
        return self._room

    async def start(self, config: HaxballConfig) -> Room:
        bridge = BrowserBridge(
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
        room = Room(bridge)
        self._bridge = bridge
        self._room = room
        return room

    async def init(self, config: HaxballConfig | dict[str, Any]) -> Room:
        if isinstance(config, dict):
            token = config.get("token")
            if not token or "YOUR_TOKEN" in str(token):
                config["token"] = input("Please enter your HaxBall token: ").strip()
            config = HaxballConfig.model_validate(config)
        elif isinstance(config, HaxballConfig):
            if not config.token or "YOUR_TOKEN" in config.token:
                config.token = input("Please enter your HaxBall token: ").strip()
        return await self.start(config)

    async def close(self) -> None:
        if self._bridge is not None:
            await self._bridge.close()
            self._bridge = None
            self._room = None

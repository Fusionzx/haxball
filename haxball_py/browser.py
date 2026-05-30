from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Callable

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .errors import HaxballBridgeError, HaxballTimeoutError


BRIDGE_JS = r"""
(() => {
  const roomEventNames = [
    'onPlayerJoin', 'onPlayerLeave', 'onTeamVictory', 'onPlayerChat',
    'onPlayerBallKick', 'onTeamGoal', 'onGameStart', 'onGameStop',
    'onPlayerAdminChange', 'onPlayerTeamChange', 'onPlayerKicked',
    'onGameTick', 'onGamePause', 'onGameUnpause', 'onPositionsReset',
    'onPlayerActivity', 'onStadiumChange', 'onRoomLink',
    'onKickRateLimitSet', 'onTeamsLockChange'
  ];

  const deepClone = (value) => JSON.parse(JSON.stringify(value));

  window.__haxpy = {
    room: null,
    eventNames: roomEventNames,
    makeRoom(config) {
      if (!window.HBInit) {
        throw new Error('HBInit is not available yet');
      }
      const room = window.HBInit(config);
      window.__haxpy.room = room;
      for (const name of roomEventNames) {
        room[name] = (...args) => {
          const payload = args.map((arg) => deepClone(arg));
          window.haxpy_emit({ event: name, args: payload }).catch(() => {});
        };
      }
      return true;
    },
    async call(method, args) {
      const room = window.__haxpy.room;
      if (!room) throw new Error('Room not initialized');
      const fn = room[method];
      if (typeof fn !== 'function') throw new Error(`Unknown room method: ${method}`);
      const result = fn.apply(room, args);
      if (result && typeof result.then === 'function') return await result;
      return result;
    },
    getState() {
      return window.__haxpy.room;
    }
  };
})();
"""


@dataclass(slots=True)
class BrowserResources:
    browser: Browser
    context: BrowserContext
    page: Page


class BrowserBridge:
    def __init__(self, *, headless: bool, proxy_server: str | None, browser_channel: str | None,
                 browser_executable_path: str | None, browser_args: list[str], timeout_ms: int) -> None:
        self.headless = headless
        self.proxy_server = proxy_server
        self.browser_channel = browser_channel
        self.browser_executable_path = browser_executable_path
        self.browser_args = browser_args
        self.timeout_ms = timeout_ms
        self._playwright = None
        self._resources: BrowserResources | None = None
        self._emit_callback: Callable[[str, list[Any]], Any] | None = None

    @property
    def page(self) -> Page:
        if not self._resources:
            raise HaxballBridgeError('Browser not started')
        return self._resources.page

    async def start(self) -> None:
        if self._resources is not None:
            return
        self._playwright = await async_playwright().start()
        chromium = self._playwright.chromium
        launch_kwargs: dict[str, Any] = {
            'headless': self.headless,
        }
        if self.browser_channel:
            launch_kwargs['channel'] = self.browser_channel
        if self.browser_executable_path:
            launch_kwargs['executable_path'] = self.browser_executable_path
        if self.browser_args:
            launch_kwargs['args'] = list(self.browser_args)
        if self.proxy_server:
            launch_kwargs['proxy'] = {'server': self.proxy_server}

        browser = await chromium.launch(**launch_kwargs)
        context = await browser.new_context()
        page = await context.new_page()
        await page.expose_binding('haxpy_emit', self._emit_from_js)
        await page.add_init_script(BRIDGE_JS)
        self._resources = BrowserResources(browser=browser, context=context, page=page)

    async def close(self) -> None:
        if self._resources is None:
            return
        try:
            await self._resources.context.close()
        finally:
            await self._resources.browser.close()
            if self._playwright is not None:
                await self._playwright.stop()
            self._resources = None
            self._playwright = None

    async def goto_headless_host(self, url: str) -> None:
        page = self.page
        await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout_ms)
        await page.wait_for_function('() => typeof window.HBInit === "function"', timeout=self.timeout_ms)

    async def create_room(self, config: dict[str, Any]) -> None:
        page = self.page
        await page.evaluate(
            """
            async ({ config }) => {
              return window.__haxpy.makeRoom(config);
            }
            """,
            {'config': config},
        )

    async def call(self, method: str, *args: Any) -> Any:
        return await self.page.evaluate(
            """
            async ({ method, args }) => {
              return await window.__haxpy.call(method, args);
            }
            """,
            {'method': method, 'args': list(args)},
        )

    def set_emit_callback(self, callback: Callable[[str, list[Any]], Any]) -> None:
        self._emit_callback = callback

    async def _emit_from_js(self, source: Any, payload: dict[str, Any]) -> None:
        if not self._emit_callback:
            return
        event = payload.get('event')
        args = payload.get('args', [])
        maybe = self._emit_callback(event, args)
        if asyncio.iscoroutine(maybe):
            await maybe

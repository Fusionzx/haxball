from __future__ import annotations
import asyncio
import json
import subprocess
import sys
import tempfile
import os
from typing import Any, Callable, Dict

class NativeEngine:
    """Executes HaxBall headless engine natively using a lightweight Node.js helper subprocess."""
    
    def __init__(self, proxy: str | None = None, debug: bool = False) -> None:
        self.proxy = proxy
        self.debug = debug
        self._process: subprocess.Popen | None = None
        self._loop = asyncio.get_event_loop()
        self._callbacks: Dict[str, Callable] = {}
        self._pending_futures: Dict[int, asyncio.Future] = {}
        self._cmd_counter = 0

    async def start(self) -> None:
        # Generate the Node.js script dynamically
        from .engine.headless_min import HEADLESS_MIN_JS
        from .engine.polyfills import JSPolyfills
        
        polyfills_code = JSPolyfills.generate(self.proxy, self.debug)
        
        node_script = f"""
        // Browser Polyfills
        {polyfills_code}
        
        // Haxball Headless Source
        {HEADLESS_MIN_JS}
        
        // Host API bindings & JSON-RPC Protocol
        const readline = require('readline');
        const rl = readline.createInterface({{
            input: process.stdin,
            output: process.stdout,
            terminal: false
        }});
        
        let room = null;
        const roomEventNames = [
            'onPlayerJoin', 'onPlayerLeave', 'onTeamVictory', 'onPlayerChat',
            'onPlayerBallKick', 'onTeamGoal', 'onGameStart', 'onGameStop',
            'onPlayerAdminChange', 'onPlayerTeamChange', 'onPlayerKicked',
            'onGameTick', 'onGamePause', 'onGameUnpause', 'onPositionsReset',
            'onPlayerActivity', 'onStadiumChange', 'onRoomLink',
            'onKickRateLimitSet', 'onTeamsLockChange'
        ];
        
        rl.on('line', (line) => {{
            try {{
                const req = JSON.parse(line);
                if (req.type === 'init') {{
                    if (typeof HBInit === 'undefined') {{
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: 'HBInit is not defined' }}) + '\\n');
                        return;
                    }}
                    room = HBInit(req.config);
                    for (const name of roomEventNames) {{
                        room[name] = (...args) => {{
                            process.stdout.write(JSON.stringify({{ type: 'event', name: name, args: args }}) + '\\n');
                        }};
                    }}
                    process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, result: true }}) + '\\n');
                }} else if (req.type === 'call') {{
                    if (!room) {{
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: 'Room not initialized' }}) + '\\n');
                        return;
                    }}
                    const method = room[req.method];
                    if (typeof method !== 'function') {{
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: 'Method not found: ' + req.method }}) + '\\n');
                        return;
                    }}
                    const res = method.apply(room, req.args);
                    process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, result: res }}) + '\\n');
                }}
            }} catch (err) {{
                process.stderr.write(err.stack + '\\n');
            }}
        }});
        """
        
        # Write to a temporary file
        self._temp_file = tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8")
        self._temp_file.write(node_script)
        self._temp_file.close()
        
        # Spawn Node.js process
        self._process = subprocess.Popen(
            ["node", self._temp_file.name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            bufsize=1
        )
        
        # Start reading stdout in background task
        asyncio.create_task(self._read_stdout())

    async def _read_stdout(self) -> None:
        loop = asyncio.get_running_loop()
        while self._process and self._process.poll() is None:
            # Run blocking read in thread pool to avoid freezing event loop
            line = await loop.run_in_executor(None, self._process.stdout.readline)
            if not line:
                break
            try:
                data = json.loads(line.strip())
                if data.get("type") == "event":
                    name = data.get("name")
                    args = data.get("args", [])
                    callback = self._callbacks.get(name)
                    if callback:
                        asyncio.create_task(callback(*args))
                elif data.get("type") == "reply":
                    req_id = data.get("id")
                    fut = self._pending_futures.pop(req_id, None)
                    if fut:
                        if "error" in data:
                            fut.set_exception(RuntimeError(data["error"]))
                        else:
                            fut.set_result(data.get("result"))
            except Exception:
                pass

    async def call(self, method: str, *args: Any) -> Any:
        self._cmd_counter += 1
        cmd_id = self._cmd_counter
        fut = self._loop.create_future()
        self._pending_futures[cmd_id] = fut
        
        payload = json.dumps({"type": "call", "id": cmd_id, "method": method, "args": list(args)}) + "\n"
        self._process.stdin.write(payload)
        self._process.stdin.flush()
        return await fut

    async def init_room(self, config: dict[str, Any], event_callback: Callable[[str, list[Any]], Any]) -> None:
        # Register event routing callback
        for name in [
            'onPlayerJoin', 'onPlayerLeave', 'onTeamVictory', 'onPlayerChat',
            'onPlayerBallKick', 'onTeamGoal', 'onGameStart', 'onGameStop',
            'onPlayerAdminChange', 'onPlayerTeamChange', 'onPlayerKicked',
            'onGameTick', 'onGamePause', 'onGameUnpause', 'onPositionsReset',
            'onPlayerActivity', 'onStadiumChange', 'onRoomLink',
            'onKickRateLimitSet', 'onTeamsLockChange'
        ]:
            self._callbacks[name] = lambda *args, n=name: event_callback(n, list(args))
            
        self._cmd_counter += 1
        cmd_id = self._cmd_counter
        fut = self._loop.create_future()
        self._pending_futures[cmd_id] = fut
        
        payload = json.dumps({"type": "init", "id": cmd_id, "config": config}) + "\n"
        self._process.stdin.write(payload)
        self._process.stdin.flush()
        await fut

    def close(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None
        try:
            os.unlink(self._temp_file.name)
        except Exception:
            pass

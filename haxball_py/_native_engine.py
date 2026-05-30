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
        self._ready_future: asyncio.Future | None = None

    async def start(self) -> None:
        # Generate the Node.js script dynamically
        from .engine.headless_min import HEADLESS_MIN_JS
        from .engine.polyfills import JSPolyfills
        
        polyfills_code = JSPolyfills.generate(self.proxy, self.debug)
        
        # Patch HEADLESS_MIN_JS: use globalThis.WebSocket to ensure scope visibility
        patched_headless = HEADLESS_MIN_JS.replace('new WebSocket(', 'new globalThis.WebSocket(')

        node_script = f"""
        // Browser Polyfills
        {polyfills_code}
        
        // Haxball Headless Source (nodeified with promiseResolve)
        {patched_headless}
        
        // Host API bindings & JSON-RPC Protocol
        const readline = require('readline');
        const rl = readline.createInterface({{
            input: process.stdin,
            output: process.stdout,
            terminal: false
        }});
        
        let room = null;
        let HBInit_fn = null;
        const roomEventNames = [
            'onPlayerJoin', 'onPlayerLeave', 'onTeamVictory', 'onPlayerChat',
            'onPlayerBallKick', 'onTeamGoal', 'onGameStart', 'onGameStop',
            'onPlayerAdminChange', 'onPlayerTeamChange', 'onPlayerKicked',
            'onGameTick', 'onGamePause', 'onGameUnpause', 'onPositionsReset',
            'onPlayerActivity', 'onStadiumChange', 'onRoomLink',
            'onKickRateLimitSet', 'onTeamsLockChange'
        ];
        const ALLOWED_METHODS = [
            'sendChat','sendAnnouncement','setPlayerAdmin','setPlayerTeam',
            'kickPlayer','clearBan','clearBans','setScoreLimit','setTimeLimit',
            'setDefaultStadium','setCustomStadium','setTeamsLock','setTeamColors',
            'startGame','stopGame','pauseGame','getPlayer','getPlayerList',
            'getScores','setPassword','setRequireRecaptcha','reorderPlayers',
            'setKickRateLimit','setPlayerAvatar','setDiscProperties',
            'getDiscProperties','setPlayerDiscProperties','getPlayerDiscProperties',
            'getDiscCount','startRecording','stopRecording'
        ];
        
        // Wait for headless engine to resolve HBInit, then signal ready
        HBInitPromise.then((fn) => {{
            HBInit_fn = fn;
            console.error('HBInit resolved successfully');
            process.stdout.write(JSON.stringify({{ type: 'ready', result: 'hbinit_ready' }}) + '\\n');
        }}).catch((err) => {{
            console.error('HBInit failed:', err.message, err.stack);
            process.stdout.write(JSON.stringify({{ type: 'ready', result: 'error', error: err.message }}) + '\\n');
        }});
        
        rl.on('line', (line) => {{
            try {{
                const req = JSON.parse(line);
                if (req.type === 'init') {{
                    if (!HBInit_fn) {{
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: 'HBInit not ready yet' }}) + '\\n');
                        return;
                    }}
                    console.error('Calling HBInit_fn with config:', JSON.stringify(req.config).substring(0, 100));
                    try {{
                        room = HBInit_fn(req.config);
                        console.error('Room created successfully');
                    }} catch(initErr) {{
                        console.error('HBInit_fn threw:', initErr.message, initErr.stack);
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: 'HBInit threw: ' + initErr.message }}) + '\\n');
                        return;
                    }}
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
                    if (!ALLOWED_METHODS.includes(req.method)) {{
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: 'Method not allowed: ' + req.method }}) + '\\n');
                        return;
                    }}
                    const method = room[req.method];
                    if (typeof method !== 'function') {{
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: 'Method not found: ' + req.method }}) + '\\n');
                        return;
                    }}
                    try {{
                        const res = method.apply(room, req.args);
                        if (res && typeof res.then === 'function') {{
                            res.then(r => {{
                                if (r instanceof Uint8Array) {{
                                    process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, result: Array.from(r) }}) + '\\n');
                                }} else {{
                                    process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, result: r }}) + '\\n');
                                }}
                            }}).catch(e => {{
                                process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: e.message }}) + '\\n');
                            }});
                        }} else {{
                            if (res instanceof Uint8Array) {{
                                process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, result: Array.from(res) }}) + '\\n');
                            }} else {{
                                process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, result: res }}) + '\\n');
                            }}
                        }}
                    }} catch (callErr) {{
                        process.stdout.write(JSON.stringify({{ type: 'reply', id: req.id, error: callErr.message }}) + '\\n');
                    }}
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
        
        # Find node_modules path (from project dir or cwd)
        node_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "node_modules")
        if not os.path.isdir(node_path):
            node_path = os.path.join(os.getcwd(), "node_modules")
        env = os.environ.copy()
        if os.path.isdir(node_path):
            env.setdefault("NODE_PATH", node_path)

        # Spawn Node.js process
        self._process = subprocess.Popen(
            ["node", self._temp_file.name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        
        # Start reading stdout/stderr in background tasks
        self._ready_future = self._loop.create_future()
        asyncio.create_task(self._read_stdout())
        asyncio.create_task(self._read_stderr())
        
        # Wait for engine ready signal (timeout 30s)
        try:
            await asyncio.wait_for(self._ready_future, timeout=30)
        except asyncio.TimeoutError:
            self.close()
            raise RuntimeError(
                "Engine did not initialize within 30 seconds. "
                "Check that Node.js and npm dependencies (pako, ws, @peculiar/webcrypto) are installed."
            )

    async def _read_stdout(self) -> None:
        loop = asyncio.get_running_loop()
        while self._process and self._process.poll() is None:
            line = await loop.run_in_executor(None, self._process.stdout.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "ready":
                    result = data.get("result")
                    if result == "error":
                        err_msg = data.get("error", "Unknown error")
                        if self._ready_future and not self._ready_future.done():
                            self._ready_future.set_exception(RuntimeError(f"Engine init failed: {err_msg}"))
                    else:
                        if self._ready_future and not self._ready_future.done():
                            self._ready_future.set_result(True)
                elif data.get("type") == "event":
                    name = data.get("name")
                    args = data.get("args", [])
                    print(f"[stdout:event] {name} ({len(args)} args)", flush=True)
                    callback = self._callbacks.get(name)
                    if callback:
                        asyncio.create_task(callback(*args))
                elif data.get("type") == "reply":
                    req_id = data.get("id")
                    print(f"[stdout:reply] id={req_id} has_result={'result' in data} error={data.get('error')}", flush=True)
                    fut = self._pending_futures.pop(req_id, None)
                    if fut:
                        if "error" in data:
                            fut.set_exception(RuntimeError(data["error"]))
                        else:
                            fut.set_result(data.get("result"))
            except Exception as ex:
                print(f"[stdout:error] Failed to parse: {line[:200]} error={ex}", flush=True)

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

    async def _read_stderr(self) -> None:
        loop = asyncio.get_running_loop()
        while self._process and self._process.poll() is None:
            line = await loop.run_in_executor(None, self._process.stderr.readline)
            if not line:
                break
            print(f"[engine:err] {line.strip()}", flush=True)

    def close(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None
        try:
            os.unlink(self._temp_file.name)
        except Exception:
            pass

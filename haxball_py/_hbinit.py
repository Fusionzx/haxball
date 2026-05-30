from __future__ import annotations
import asyncio
from typing import Any, Callable, Dict
from ._native_engine import NativeEngine
from .room_native import RoomNative

# Keep global cache of engines
_engine_instance: NativeEngine | None = None
_hb_init_future: asyncio.Future[Callable] | None = None

async def HaxballJS(config: Dict[str, Any] | None = None) -> Callable[[Dict[str, Any]], RoomNative]:
    """Bootstraps HaxBall engine natively (Backend B) and returns a callable to initialize rooms.
    Allows exact replication of:
        const HBInit = await HaxballJS({ ... });
        const room = HBInit({ roomName: "Room", ... });
    """
    global _engine_instance, _hb_init_future
    
    if _hb_init_future is None:
        _hb_init_future = asyncio.get_event_loop().create_future()
        
        cfg = config or {}
        proxy = cfg.get("proxy")
        debug = cfg.get("debug", False)
        
        engine = NativeEngine(proxy=proxy, debug=debug)
        await engine.start()
        _engine_instance = engine
        
        def hb_init_callable(room_cfg: Dict[str, Any]) -> RoomNative:
            room = RoomNative(engine)
            
            # Start initialization on the engine side
            asyncio.create_task(
                engine.init_room(room_cfg, room._handle_js_event)
            )
            return room
            
        _hb_init_future.set_result(hb_init_callable)
        
    return await _hb_init_future

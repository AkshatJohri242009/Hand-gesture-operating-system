import asyncio
import json
import logging
import threading
import time

from shared.events import bus, Event

logger = logging.getLogger(__name__)

try:
    import websockets
    from websockets.asyncio.server import serve as ws_serve

    HAS_WS = True
except ImportError:
    HAS_WS = False


class HUDWebSocketBridge:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: set = set()
        self._thread: threading.Thread | None = None
        self._server = None
        self._loop = None
        self._running = False

    def start(self):
        if not HAS_WS:
            logger.warning("websockets not installed — HUD bridge disabled")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="hud-ws")
        self._thread.start()
        bus.subscribe_all(self._on_any_event, "hud-bridge")
        logger.info("HUD bridge starting on ws://%s:%d", self.host, self.port)

    def _run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._serve())
        except RuntimeError:
            pass
        finally:
            loop.close()

    async def _serve(self):
        self._server = await ws_serve(self._handler, self.host, self.port)
        self._loop = asyncio.get_running_loop()
        try:
            await self._server.serve_forever()
        except asyncio.CancelledError:
            pass
        finally:
            self._server.close()
            await self._server.wait_closed()

    async def _handler(self, websocket):
        self._clients.add(websocket)
        try:
            async for _ in websocket:
                pass
        except:
            pass
        finally:
            self._clients.discard(websocket)

    def _on_any_event(self, event: Event):
        if not self._clients or not self._loop or not self._running:
            return
        msg = json.dumps({
            "topic": event.topic,
            "payload": event.payload,
            "source": event.source,
            "timestamp": event.timestamp,
        })
        asyncio.run_coroutine_threadsafe(self._broadcast(msg), self._loop)

    async def _broadcast(self, msg: str):
        if not self._clients:
            return
        dead = set()
        for ws in self._clients:
            try:
                await ws.send(msg)
            except:
                dead.add(ws)
        self._clients -= dead

    def stop(self):
        self._running = False
        bus.unsubscribe("hud-bridge")
        if self._server:
            self._server.close()
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("HUD bridge stopped")

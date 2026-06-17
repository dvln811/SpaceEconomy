import asyncio
import logging
from aiohttp import web
from server.config import TICK_RATE, HOST, PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("space_economy")

clients: set[web.WebSocketResponse] = set()


async def economy_tick():
    """Real-time economy loop. Runs forever at TICK_RATE."""
    tick = 0
    while True:
        tick += 1
        # TODO: economy simulation step here
        log.info(f"tick {tick}")
        await asyncio.sleep(TICK_RATE)


async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    clients.add(ws)
    log.info(f"client connected ({len(clients)} total)")
    try:
        async for msg in ws:
            pass  # TODO: handle client messages
    finally:
        clients.discard(ws)
        log.info(f"client disconnected ({len(clients)} total)")
    return ws


async def health(request):
    return web.Response(text="ok")


def create_app():
    app = web.Application()
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/health", health)
    return app


async def main():
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    actual_port = site._server.sockets[0].getsockname()[1]
    log.info(f"server listening on {HOST}:{actual_port}")
    await economy_tick()


if __name__ == "__main__":
    asyncio.run(main())

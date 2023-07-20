import asyncio
from contextlib import suppress

from client import BlockstreamClient
import logging
from aiohttp import web
from os import environ

REDIS_HOST = environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = environ.get("REDIS_PORT", default="6379")
TEST = bool(environ.get("BTC_TEST", default=False))

bitcoin_client = BlockstreamClient(f"{REDIS_HOST}:{REDIS_PORT}", TEST)

logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO
)

app = web.Application()
routes = web.RouteTableDef()

logging.info(REDIS_HOST)
logging.info(REDIS_PORT)
logging.info(TEST)


@routes.get("/")
async def index(request):
    tip, hash = await bitcoin_client.get_tip()
    return web.json_response({"status": "ok", "tip": tip, "hash": hash})


@routes.get("/next")
async def get_tip(request):
    if TEST:
        await bitcoin_client.next_block()
        return web.json_response({"message": "completed"})
    else:
        return web.json_response({"message": "rejected in non-test setup"})


@routes.get("/reset")
async def get_tip(request):
    if TEST:
        return web.json_response({"message": "completed"})
        await bitcoin_client.reset()
        return web.json_response({"message": "completed"})
    else:
        return web.json_response({"message": "rejected in non-test setup"})


@routes.get("/tip")
async def get_tip(request):
    tip, _ = await bitcoin_client.get_tip()
    if not tip:
        if tip == 0:
            return web.json_response(tip)
        else:
            return web.json_response({"message": "error with request"})
    return web.json_response(tip)


@routes.get("/tip/hash")
async def get_tip(request):
    _, hash = await bitcoin_client.get_tip()
    if not hash:
        if hash == "":
            return web.json_response(hash)
        else:
            return web.json_response({"message": "error with request"})
    return web.json_response(hash)


@routes.get("/block")
async def get_block(request):
    if "hash" in request.query.keys():
        data = await bitcoin_client.get_block(request.query["hash"])
        return web.json_response(data)
    else:
        return web.json_response({"message": "error with request"})


@routes.get("/block/status/<hash>")
async def get_block_status(request, hash):
    data = await bitcoin_client.get_block_status(hash)
    if not data:
        return web.json_response({"message": "error with request"})
    return data


@routes.get("/lastblocks")
async def get_all_blocks(request):
    data = await bitcoin_client.get_all_blocks()
    if not data:
        return web.json_response({"message": "error with request"})

    return data


async def background_tasks(app):
    app["btc_worker"] = asyncio.create_task(bitcoin_client.sync_tip())

    yield

    app["btc_worker"].cancel()
    with suppress(asyncio.CancelledError):
        await app["btc_worker"]  # Ensure any exceptions etc. are raised.


app.router.add_routes(routes)

if __name__ == "__main__":
    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, port=5001)

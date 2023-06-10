import asyncio
from contextlib import suppress

from client import BlockstreamClient
import logging
from aiohttp import web
from os import environ

REDIS_HOST = environ.get("host", default="0.0.0.0")
REDIS_PORT = environ.get("port", default="6379")

bitcoin_client = BlockstreamClient(f"{REDIS_HOST}:{REDIS_PORT}")

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)

app = web.Application()
routes = web.RouteTableDef()


@routes.get("/")
async def index(request):
    tip, hash = await bitcoin_client.get_tip()
    return web.json_response({"status": "ok", "tip": tip, "hash": hash})


@routes.get("/tip")
async def get_current_hash(request):
    hash = await bitcoin_client.get_current_hash()
    if not hash:
        return web.json_response({'message': 'error with request'})
    return web.json_response({"tip": hash})


@routes.get("/block")
async def get_block(request):
    if "hash" in request.query.keys():
        data = await bitcoin_client.get_block(request.query["hash"])
        return web.json_response(data)
    else:
        return web.json_response({'message': 'error with request'})


@routes.get("/block/status/<hash>")
async def get_block_status(request, hash):
    data = await bitcoin_client.get_block_status(hash)
    if not data:
        return web.json_response({'message': 'error with request'})
    return data


@routes.get("/lastblocks")
async def get_all_blocks(request):
    data = await bitcoin_client.get_all_blocks()
    if not data:
        return web.json_response({'message': 'error with request'})

    return data


async def background_tasks(app):
    app['btc_worker'] = asyncio.create_task(bitcoin_client.sync_tip())

    yield

    app['btc_worker'].cancel()
    with suppress(asyncio.CancelledError):
        await app['btc_worker']  # Ensure any exceptions etc. are raised.

app.router.add_routes(routes)

if __name__ == "__main__":

    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, port=5001)

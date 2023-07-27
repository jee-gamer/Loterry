"""
This file contains implementation for Block explorers clients.
"""
import logging
import asyncio
import json

import aiohttp
import redis.asyncio as redis


logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO
)

class BlockstreamClient:
    """
    This is the client from Blockstream.info block explorer which implements
    Esplora API for providing chain and address information
    """
    _base_path = "https://blockstream.info/api"
    _recent_blocks = None
    _tip = 0
    _tip_hash = ""
    _redis = None
    _test = False

    def __init__(self, redis_uri="localhost:6379", test=False, test_blocks=None):
        self._test = test
        host, port = redis_uri.split(":")
        logging.info("Redis URI: %s, test %s", redis_uri, test)
        self._redis = redis.Redis(host=host, port=port, db=0)

        if not test_blocks:
            with open("./tests/data/blocks.json", "rb") as fblocks:
                test_blocks = json.loads(fblocks.read())

        if self._test and test_blocks:
            self._recent_blocks = sorted(test_blocks, key=lambda b: b["height"])
        elif self._test and not test_blocks:
            raise ValueError("The list test_blocks should not be empty")
        else:
            pass

    async def make_request(self, endpoint, method="GET", **kwargs):
        """
        Wrapper method for HTTP requests
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self._base_path}{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    if response.headers.get("Content-Type") == "text/plain":
                        data = await response.text()
                        logging.debug("from BcClient %s", data)
                    elif response.headers.get("Content-Type") == "application/json":
                        data = await response.json()
                        logging.debug("from BcClient %s", data)
                    else:
                        logging.error("Can't obtain json or text")
                return data

    async def reset(self):
        """
        Facilitates block height reset and re-reads test block data json
        """
        if self._test:
            with open("./tests/data/blocks.json", "rb") as reset_json:
                self._recent_blocks = sorted(
                    json.loads(reset_json.read()),
                    key=lambda b: b["height"])
            self._tip = self._recent_blocks[-1]["height"]
            self._tip_hash = self._recent_blocks[-1]["id"]
        else:
            pass

    async def next_block(self):
        """
        Roll over recent blocks to some next block in the list but with higher
        height
        """
        self._tip = self._tip + 1
        block = self._recent_blocks.pop()
        block["height"] = self._tip
        self._recent_blocks.insert(0, block)
        self._tip_hash = block["id"]
        await self._redis.publish("blocks", json.dumps(block))
        logging.info("Sent to redis %s/%s", self._tip_hash, self._tip)
        return self._tip, self._tip_hash

    async def get_tip(self):
        """
        Client highest actual block
        """
        return self._tip, self._tip_hash

    async def get_network_info(self):
        """
        All blocks that currently visible from client
        """
        return self._recent_blocks

    async def get_current_hash(self):
        """
        Returs tip block hash id
        """
        if self._test:
            return self._tip_hash
        endpoint = "/blocks/tip/hash"
        return await self.make_request(endpoint)

    async def get_block(self, blockhash):
        """
        Returns block info by its hash
        """
        endpoint = f"/block/{blockhash}"
        return await self.make_request(endpoint)

    async def get_block_status(self, blockhash):
        """
        Returns block height and information if it is included into main chain
        (not on the forked chain)
        """
        endpoint = f"/block/{blockhash}/status"
        return await self.make_request(endpoint)

    async def get_all_blocks(self):
        """
        Returns 10 latest blocks
        """
        endpoint = "/blocks/tip"
        return await self.make_request(endpoint)

    async def get_last_height(self) -> int:
        """
        Returns network the latest block number also known as height
        """
        endpoint = "/blocks/tip/height"
        return int(await self.make_request(endpoint))

    async def sync_tip(self):
        """
        Performs synchronization with Explorer API
        """
        if not await self._redis.ping():
            logging.error("No connection with redis")
            raise ConnectionError("No connection with redis")

        while True:
            try:
                if not self._test:
                    self._recent_blocks = await self.get_all_blocks()
                for block in sorted(self._recent_blocks, key=lambda b: b["height"]):
                    if self._tip == 0 or block["height"] > self._tip:
                        self._tip = block["height"]
                        self._tip_hash = block["id"]
                        await self._redis.publish("blocks", json.dumps(block))
                        logging.info("Sent to redis %s/%s", self._tip, self._tip_hash)
                        await asyncio.sleep(0.01)
                    else:
                        continue
                logging.info("Synced %s/%s", self._tip, self._tip_hash)
                if self._test:
                    logging.info("Client is in test mode, exiting sync_tip routine")
                    return
            except Exception as sync_exception:
                logging.info(sync_exception)
            await asyncio.sleep(300)


if __name__ == "__main__":
    with open("tests/data/blocks.json", "rb") as json_blocks:
        blocks = json.loads(json_blocks.read())
    client = BlockstreamClient(test=True, test_blocks=blocks)
    tip, block_hash = asyncio.run(client.get_tip())
    print(f"Test configuration: {tip}, {block_hash}")
    try:
        asyncio.run(client.sync_tip())
    except KeyboardInterrupt:
        logging.info("Sync interrupted. Exiting")
    tip, block_hash = asyncio.run(client.get_tip())
    print(f"Test configuration: {tip}, {block_hash}")
    tip, block_hash = asyncio.run(client.next_block())
    print(f"Test configuration: {tip}, {block_hash}")

    client = BlockstreamClient()
    currentHash = asyncio.run(client.get_current_hash())
    asyncio.run(client.get_block_status(currentHash))
    try:
        asyncio.run(client.sync_tip())
    except KeyboardInterrupt:
        logging.info("Sync interrupted. Exiting")

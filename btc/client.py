import asyncio
import json

import aiohttp
import redis.asyncio as redis

import logging

logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO
)


class BlockstreamClient:
    _base_path = "https://blockstream.info/api"
    _recent_blocks = []
    _tip = 0
    _tip_hash = ""
    _redis = None
    _test = False

    def __init__(self, redis_uri="localhost:6379", test=False, test_blocks=[]):
        self._test = test
        host, port = redis_uri.split(":")
        logging.info(f"Redis URI client: {redis_uri}")
        self._redis = redis.Redis(host=host, port=port, db=0)

        if not test_blocks:
            with open("./tests/data/blocks.json") as f:
                test_blocks = json.loads(f.read())

        if self._test and test_blocks:
            self._recent_blocks = sorted(test_blocks, key=lambda b: b["height"])
        elif self._test and not test_blocks:
            raise ValueError("The list test_blocks should not be empty")
        else:
            pass

    async def make_request(self, endpoint, method="GET", **kwargs):
        async with aiohttp.ClientSession() as session:
            url = f"{self._base_path}{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    if response.headers.get("Content-Type") == "text/plain":
                        try:
                            data = await response.text()
                            logging.debug(f"from BcClient {data}")
                        except Exception as e:
                            logging.error(f"Can't obtain json {e}")
                    else:
                        try:
                            data = await response.json()
                            logging.debug(f"from BcClient {data}")
                        except Exception as e:
                            logging.error(f"Can't obtain json {e}")

                return data

    async def reset(self):
        if self._test:
            with open("./tests/data/blocks.json") as f:
                self._recent_blocks = sorted(json.loads(f.read()), key=lambda b: b["height"])
            self._tip = self._recent_blocks[-1]["height"]
            self._tip_hash = self._recent_blocks[-1]["id"]
        else:
            pass

    async def next_block(self):
        # Roll over recent blocks to some next block in the list but with higher height
        self._tip = self._tip + 1
        block = self._recent_blocks.pop()
        block["height"] = self._tip
        self._recent_blocks.insert(0, block)
        self._tip_hash = block["id"]
        await self._redis.publish("blocks", json.dumps(block))
        logging.info(f"Sent to redis {self._tip_hash}/{self._tip}")
        return self._tip, self._tip_hash

    async def get_tip(self):
        return self._tip, self._tip_hash

    async def get_network_info(self):
        return self._recent_blocks

    async def get_current_hash(self):
        if self._test:
            return self._tip_hash
        endpoint = "/blocks/tip/hash"
        return await self.make_request(endpoint)

    async def get_block(self, hash):
        endpoint = f"/block/{hash}"
        return await self.make_request(endpoint)

    async def get_block_status(self, hash):
        endpoint = f"/block/{hash}/status"
        return await self.make_request(endpoint)

    async def get_all_blocks(self):
        endpoint = "/blocks/tip"
        return await self.make_request(endpoint)

    async def get_last_height(self) -> int:
        endpoint = "/blocks/tip/height"
        return int(await self.make_request(endpoint))

    async def sync_tip(self):
        if not await self._redis.ping():
            raise ConnectionError("No connection with redis")
        else:
            logging.info("Redis pinged. Started syncing")
        while True:
            try:
                if not self._test:
                    self._recent_blocks = await self.get_all_blocks()
                for b in sorted(self._recent_blocks, key=lambda b: b["height"]):
                    if self._tip == 0 or b["height"] > self._tip:
                        self._tip = b["height"]
                        self._tip_hash = b["id"]
                        await self._redis.publish("blocks", json.dumps(b))
                        logging.info(f"Sent to redis {self._tip}/{self._tip_hash}")
                        await asyncio.sleep(0.01)
                    else:
                        continue
                logging.info(f"Synced {self._tip}/{self._tip_hash}")
                if self._test:
                    logging.info("Client is in test mode, exiting sync_tip routine")
                    return
            except Exception as e:
                logging.info(e)
                pass
            await asyncio.sleep(300)


if __name__ == "__main__":
    with open("tests/data/blocks.json", "r") as f:
        test_blocks = json.loads(f.read())
    client = BlockstreamClient(test=True, test_blocks=test_blocks)
    tip, hash = asyncio.run(client.get_tip())
    print(f"Test configuration: {tip}, {hash}")
    try:
        asyncio.run(client.sync_tip())
    except KeyboardInterrupt:
        logging.info("Sync interrupted. Exiting")
    tip, hash = asyncio.run(client.get_tip())
    print(f"Test configuration: {tip}, {hash}")
    tip, hash = asyncio.run(client.next_block())
    print(f"Test configuration: {tip}, {hash}")

    client = BlockstreamClient()
    currentHash = asyncio.run(client.get_current_hash())
    asyncio.run(client.get_block_status(currentHash))
    try:
        asyncio.run(client.sync_tip())
    except KeyboardInterrupt:
        logging.info("Sync interrupted. Exiting")

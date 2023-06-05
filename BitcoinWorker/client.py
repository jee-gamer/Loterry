import asyncio
import json

import aiohttp
import redis.asyncio as redis


class BlockstreamClient:
    _base_path = "https://blockstream.info/api"
    _recent_blocks = []
    _tip = 0
    _tip_hash = ""
    _redis = None

    def __init__(self, redis_uri="localhost:6379"):
        host, port = redis_uri.split(":")
        print(f"Redis URI: {redis_uri}")
        self._redis = redis.Redis(host=host, port=port, db=0)

    async def make_request(self, endpoint, method="GET", **kwargs):
        async with aiohttp.ClientSession() as session:
            url = f"{self._base_path}{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                    except Exception as e:
                        print(f"Can't obtain json {e}")
                return data

    async def get_tip(self):
        return self._tip, self._tip_hash

    async def get_network_info(self):
        return self._recent_blocks

    async def get_current_hash(self):
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
            print("Redis pinged. Started syncing")
        while True:
            try:
                blocks = await self.get_all_blocks()
                for b in sorted(blocks, key=lambda b: b["height"]):
                    if self._tip == 0 or b["height"] > self._tip:
                        self._tip = b["height"]
                        self._tip_hash = b["id"]
                        print(f"Sent to redis {self._tip}/{self._tip_hash}")
                        await self._redis.publish("blocks", json.dumps(b))
                        await asyncio.sleep(0.01)
                    else:
                        continue
                print(f"Synced {self._tip}/{self._tip_hash}")
            except Exception as e:
                print(e)
                pass
            await asyncio.sleep(600)


if __name__ == "__main__":
    client = BlockstreamClient()
    currentHash = asyncio.run(client.get_current_hash())
    asyncio.run(client.get_block_status(currentHash))
    try:
        asyncio.run(client.sync_tip())
    except KeyboardInterrupt:
        print("Sync interrupted. Exiting")

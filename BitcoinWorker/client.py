import asyncio
import json

from requests import get
import redis.asyncio as redis


class BlockstreamClient:
    _base_path = "https://blockstream.info/api"
    _recent_blocks = []
    _tip = 0
    _tip_hash = ""
    _redis = None

    def __init__(self, redis_uri=None):
        if redis_uri and ":" in redis_uri:
            host, port = redis_uri.split(":")
            self._redis = redis.Redis(host=host, port=port, db=0)
        else:
            self._redis = redis.Redis(host="localhost", port=6379, db=0)


    async def make_request(self, endpoint):
        try:
            #
            response = get(f"{self._base_path}{endpoint}")
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return response.text
            else:
                print(f"Can't request Blockstream: {response.status_code}")
        except Exception as e:
            print(f"Can't make a request {e}")
        return None

    async def get_tip(self):
        return self._tip, self._tip_hash

    async def get_networkinfo(self):
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

    async def get_all_block(self):
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
                tip = await self.get_all_block()
                if tip and self._tip != tip[0]["height"]:  # if tip exist and the current height isn't equal
                    self._tip = tip[0]["height"]
                    self._tip_hash = tip[0]["id"]
                    await self._redis.publish("blocks", json.dumps(tip))

                all_block = await self.get_all_block()

                if all_block:
                    self._recent_blocks = all_block

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

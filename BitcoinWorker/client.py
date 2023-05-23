import asyncio
from requests import get


class BlockstreamClient:

    _base_path = "https://blockstream.info/api"
    _recent_blocks = []

    def __init__(self):
        pass

    async def make_request(self, endpoint):
        try:
            #
            response = get(f"{self._base_path}{endpoint}")
            if response.status_code == 200:
                data = response.text
                print(data)
                return data
            else:
                print(f"Can't request Blockstream: {response.status_code}")
        except Exception as e:
            print(f"Can't make a request {e}")
        return None

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
        while True:
            await asyncio.sleep(600)
            all_block = await self.get_all_block()

            if all_block:
                self._recent_blocks = all_block


if __name__ == "__main__":
    client = BlockstreamClient()
    currentHash = asyncio.run(client.get_current_hash())
    asyncio.run(client.get_block_status(currentHash))


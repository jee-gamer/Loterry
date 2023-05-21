import asyncio
from requests import get, post


class BlockstreamClient:

    _base_path = "https://blockstream.info/api"
    _recent_blocks = []

    def __init__(self):
        pass

    async def get_current_hash(self):
        try:
            #
            uri = f"{self._base_path}/blocks/tip/hash"
            response = get(uri)
            if response.status_code == 200:
                data = response.text
                print(data)
                return data
            else:
                print(f"Can't request Blockstream: {response.status_code}")
        except Exception as e:
            print(f"Can't make a request {e}")
        return False

    async def get_block(self, hash):
        try:
            #
            uri = f"{self._base_path}/block/{hash}"
            response = get(uri)
            if response.status_code == 200:
                data = response.json()
                print(data)
                return data
            else:
                print(f"Can't request Blockstream: {response.status_code}")
        except Exception as e:
            print(f"Can't make a request {e}")
        return False


    async def get_block_status(self, hash):
        try:
            #
            uri = f"{self._base_path}/block/{hash}/status"
            response = get(uri)
            if response.status_code == 200:
                data = response.json()
                print(data)
                return data
            else:
                print(f"Can't request Blockstream: {response.status_code}")
        except Exception as e:
            print(f"Can't make a request {e}")
        return False

    async def get_all_block(self):
        try:
            #
            uri = f"{self._base_path}/blocks"
            response = get(uri)
            if response.status_code == 200:
                data = response.json()
                print(data)
                return data
            else:
                print(f"Can't request Blockstream: {response.status_code}")
        except Exception as e:
            print(f"Can't make a request {e}")
        return False

    async def get_tip(self):
        while True:
            await asyncio.sleep(600)
            all_block = await self.get_all_block()

            if self._recent_blocks != all_block:
                self._recent_blocks = all_block
            return


if __name__ == "__main__":
    client = BlockstreamClient()
    currentHash = asyncio.run(client.get_current_hash())
    asyncio.run(client.get_block_status(currentHash))

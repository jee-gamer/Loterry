import asyncio
from requests import get, post


async def get_current_hash():
    try:
        #
        base_path = "https://blockstream.info/api"
        uri = f"{base_path}/blocks/tip/hash"
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


async def get_block(hash):
    try:
        #
        base_path = "https://blockstream.info/api"
        uri = f"{base_path}/block/{hash}"
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


async def get_block_status(hash):
    try:
        #
        base_path = "https://blockstream.info/api"
        uri = f"{base_path}/block/{hash}/status"
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

async def get_alL_block():
    try:
        #
        base_path = "https://blockstream.info/api"
        uri = f"{base_path}/blocks"
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

if __name__ == "__main__":
    currentHash = asyncio.run(get_current_hash())
    asyncio.run(get_block_status(currentHash))

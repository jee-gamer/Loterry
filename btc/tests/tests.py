import asyncio
import json
import unittest
from os import environ
from btc.client import BlockstreamClient


async def tip_any():
    with open("data/blocks.json", "r") as f:
        blocks_test_vector = json.loads(f.read())
    tip = 797000
    tip_hash = 12313132323
    for b in reversed(blocks_test_vector):
        if tip == 0:
            tip = b["height"]
            tip_hash = b["id"]
            print(f"Sent to redis {tip}/{tip_hash}")
        elif b["height"] > tip:
            tip = b["height"]
            tip_hash = b["id"]
            print(f"Catch up {tip}/{tip_hash}")
        else:
            continue
    print(f"Synced with {tip}/{tip_hash}")
    assert 797947 == tip
    return True


class TestBtcWorkerTestSetup(unittest.IsolatedAsyncioTestCase):
    REDIS_HOST = environ.get("REDIS_HOST", default="localhost")
    REDIS_PORT = environ.get("REDIS_PORT", default="6379")
    test_client = BlockstreamClient(f"{REDIS_HOST}:{REDIS_PORT}", True)

    async def test_tip(self):
        await self.test_client.sync_tip()
        tip, _ = await self.test_client.get_tip()
        assert 797947 == tip

    # test get current hash here

if __name__ == "__main__":
    unittest.main()

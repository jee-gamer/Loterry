import asyncio
import json
import unittest


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


class TestStuff(unittest.IsolatedAsyncioTestCase):
    async def test_zero(self):
        r = await tip_any()
        self.assertTrue(r)



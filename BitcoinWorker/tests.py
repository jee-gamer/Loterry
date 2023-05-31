import asyncio
import json
import unittest


async def tip_any():
    blocks_test_vector = json.loads('[{"id": "00000000000000000004caa30effca32112724eba280595c79225dd018b9942a", "height": 792116, "version": 541065216, "timestamp": 1685458560, "tx_count": 3050, "size": 1577402, "weight": 3992963, "merkle_root": "6c98e19d73abce04b481c79ac030ff1508d3b3e3b9c562739c59fd1bdc78c471", "previousblockhash": "00000000000000000004380b38eb25604a06655abc444bc0db5ae4d1c1c76908", "mediantime": 1685454832, "nonce": 100140044, "bits": 386248250, "difficulty": 49549703178592}, {"id": "00000000000000000004380b38eb25604a06655abc444bc0db5ae4d1c1c76908", "height": 792115, "version": 536887296, "timestamp": 1685458507, "tx_count": 3175, "size": 1593127, "weight": 3993004, "merkle_root": "57b8f4ed20d50e98fc03dc9aed9461d61b270f5566d5d49eaae8660b45209780", "previousblockhash": "000000000000000000001f43e5a1ed1046ef9d12b4a061b0746104f58d20b67e", "mediantime": 1685454253, "nonce": 127099803, "bits": 386248250, "difficulty": 49549703178592}, {"id": "000000000000000000001f43e5a1ed1046ef9d12b4a061b0746104f58d20b67e", "height": 792114, "version": 765591552, "timestamp": 1685456596, "tx_count": 3553, "size": 1494324, "weight": 3992760, "merkle_root": "4c333365fe1a508af137632815fe6db19df4d07dcb53ecfd5e7cf09686080998", "previousblockhash": "0000000000000000000472ea5e96074dc7bac9a56ced37801f2c5d086deb5ee7", "mediantime": 1685453752, "nonce": 2244957273, "bits": 386248250, "difficulty": 49549703178592}, {"id": "0000000000000000000472ea5e96074dc7bac9a56ced37801f2c5d086deb5ee7", "height": 792113, "version": 1073733632, "timestamp": 1685455237, "tx_count": 3510, "size": 1707586, "weight": 3997927, "merkle_root": "385eb4fae9b5b132a60496275fb8324d3aa61435faf757b2fccab94419d567d8", "previousblockhash": "00000000000000000003d43d67f02c06a2a7dba02a0ae76cfaebe12809e606ce", "mediantime": 1685452647, "nonce": 1826097642, "bits": 386248250, "difficulty": 49549703178592}, {"id": "00000000000000000003d43d67f02c06a2a7dba02a0ae76cfaebe12809e606ce", "height": 792112, "version": 536911872, "timestamp": 1685454873, "tx_count": 3054, "size": 1527125, "weight": 3993173, "merkle_root": "abb2cfba9d8ce4146a001bdff8f2a50bef074e4c0d2a72b817583ae30bc86f7a", "previousblockhash": "000000000000000000013877a9652ffbc579974b7bbda120ae55cb12c97f9e74", "mediantime": 1685451042, "nonce": 136561577, "bits": 386248250, "difficulty": 49549703178592}, {"id": "000000000000000000013877a9652ffbc579974b7bbda120ae55cb12c97f9e74", "height": 792111, "version": 553246720, "timestamp": 1685454832, "tx_count": 3472, "size": 1813974, "weight": 3992613, "merkle_root": "0c38e823ce0cb71743478903f34a4a3f777ad9aa4553b4d2ceeabbdf1743d302", "previousblockhash": "0000000000000000000158ed983fd9fb25385a372cdc92fc6451b457718ad0e3", "mediantime": 1685450862, "nonce": 753172738, "bits": 386248250, "difficulty": 49549703178592}, {"id": "0000000000000000000158ed983fd9fb25385a372cdc92fc6451b457718ad0e3", "height": 792110, "version": 545259520, "timestamp": 1685454253, "tx_count": 3756, "size": 1622306, "weight": 3997769, "merkle_root": "8ce9ef3aeb37f7b786bcaaf9e049b2aaae7014f8aefc0bd2bd127904027b918e", "previousblockhash": "00000000000000000000e8db4e15385bf6844eeeb65a31e0244c0378a1502750", "mediantime": 1685450147, "nonce": 3823425091, "bits": 386248250, "difficulty": 49549703178592}, {"id": "00000000000000000000e8db4e15385bf6844eeeb65a31e0244c0378a1502750", "height": 792109, "version": 547356672, "timestamp": 1685453752, "tx_count": 3745, "size": 1607979, "weight": 3993225, "merkle_root": "15ae4dfb466fdcba43aa2925b57e6c46cfb26b7b6ff704af9272cbcfe92f8d76", "previousblockhash": "000000000000000000000dd3be3f30032be8a773025d6f01a40f30315d3fe85c", "mediantime": 1685449910, "nonce": 1803617124, "bits": 386248250, "difficulty": 49549703178592}, {"id": "000000000000000000000dd3be3f30032be8a773025d6f01a40f30315d3fe85c", "height": 792108, "version": 536887296, "timestamp": 1685452647, "tx_count": 3345, "size": 1639435, "weight": 3993013, "merkle_root": "bc4a1479604ee3362d459003b7d7443768b4c70c441f75c753efaa19674ec390", "previousblockhash": "00000000000000000005246579ff4ed05637b3046bd1ffa63dee013c9009674b", "mediantime": 1685449865, "nonce": 260300569, "bits": 386248250, "difficulty": 49549703178592}, {"id": "00000000000000000005246579ff4ed05637b3046bd1ffa63dee013c9009674b", "height": 792107, "version": 549642240, "timestamp": 1685451042, "tx_count": 2425, "size": 1482641, "weight": 3993365, "merkle_root": "b26144792fcb5a141149ccb72d6af0ca43a95ff11137a2ee7cba286ffe715945", "previousblockhash": "000000000000000000038e4c661c67b17f3f7fc3920e93d1d32b31ae3c31f276", "mediantime": 1685449127, "nonce": 1856005444, "bits": 386248250, "difficulty": 49549703178592}]')
    tip = 792113
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
    print(f"Synced {tip}/{tip_hash}")
    await asyncio.sleep(0.1)
    return True


class TestStuff(unittest.IsolatedAsyncioTestCase):
    async def test_zero(self):
        r = await tip_any()
        self.assertTrue(r)




import aiohttp
import asyncio


class BackendClient:
    def __init__(self):
        self.DATABASE_URL = "http://localhost:5000/api"

    def get_base_url(self):
        return self.DATABASE_URL

    async def make_request(self, method, endpoint, **kwargs):
        async with aiohttp.ClientSession() as session:
            url = f"{self.DATABASE_URL}{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                data = await response.json()
                return data

    # async def time_left(self, idLottery):
    #     endpoint = f"/lottery/timeLeft?idLottery={idLottery}"
    #     return await self.make_request('GET', endpoint)

    async def get_height(self, idLottery):
        endpoint = f"/lottery/height?idLottery={idLottery}"
        return await self.make_request('GET', endpoint)

    async def winning_fruit(self, idLottery):
        endpoint = f"/lottery/winningFruit?idLottery={idLottery}"
        return await self.make_request('GET', endpoint)

    async def start_lottery(self):
        endpoint = "/lottery"
        return await self.make_request('POST', endpoint)

    async def get_winners(self, idLottery):
        endpoint = f"/lottery/winners?idLottery={idLottery}"
        return await self.make_request('GET', endpoint)

    async def get_id_lottery(self):
        endpoint = "/lottery/running"
        return await self.make_request('GET', endpoint)

    async def stop_lottery(self):
        endpoint = "/lottery/stop"
        return await self.make_request('POST', endpoint)

    async def post_bet(self, idUser, idLottery, userBet):
        endpoint = "/users/vote"
        data = {
            "idUser": idUser,
            "idLottery": idLottery,
            "userBet": userBet
        }
        return await self.make_request('POST', endpoint, json=data)

    ''' HOW TO POST WITH DATA >>>
    
            async with session.post(f"{DATABASE_URL}/lottery", json=lottery_data) as response:
    '''
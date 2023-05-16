
import aiohttp
import asyncio


class BackendClient:
    def __init__(self):
        self.DATABASE_URL = "http://localhost:5000/api"

    def get_base_url(self):
        return self.DATABASE_URL

    async def time_left(self, idLottery):
        print(f"what is timeleft?")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.DATABASE_URL}/lottery/timeLeft?idLottery={idLottery}") as response:
                data = await response.json()  # Parse the response JSON
                print(f"timeLeft is {data}")
                return data

                # if response.status == 200:
                #     data = await response.json()  # Parse the response JSON
                #     print(data)
                #     return data
                # else:
                #     return 'Error: ' + str(response.status)

    async def winning_fruit(self, idLottery):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.DATABASE_URL}/lottery/winningFruit?idLottery={idLottery}") as response:
                data = await response.json()  # Parse the response JSON
                print(data)
                return data

    async def start_lottery(self):  # now returns lottery info if it did start one
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.DATABASE_URL}/lottery") as response:
                data = await response.json()
                print(data)
                if "message" in data:
                    return None
                return data

    async def get_winners(self, idLottery):
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.DATABASE_URL}/lottery/winners?idLottery={idLottery}") as response:
                data = await response.json()
                print(f"Winner is {data}")
                if not data:
                    return False
                return data

    async def get_id_lottery(self):
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.DATABASE_URL}/lottery/running") as response:
                data = await response.json()
                print(f"Lottery id {data} running")
                return data

    async def stop_lottery(self):
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.DATABASE_URL}/lottery/stop") as response:
                data = await response.json()
                print(data)

    async def post_bet(self, idUser, idLottery, userBet):
        data = None
        vote = {
            "idUser": idUser,
            "idLottery":  idLottery,
            "userBet": userBet
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.DATABASE_URL}/users_vote", json=vote) as response:
                data = await response.json()
                print(data)
        return data

    ''' HOW TO POST WITH DATA >>>
    
            async with session.post(f"{DATABASE_URL}/lottery", json=lottery_data) as response:
    '''
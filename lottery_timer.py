import time
from datetime import datetime
import aiohttp
from os import environ
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from Database.backendClient import BackendClient
client = BackendClient()

DATABASE_URL = "http://localhost:5000/api"


class LotteryTimer:
    def __init__(self, bot: Bot):
        super().__init__()
        self.active_lotteries = {}  # dictionary to store active lotteries with their end times
        self.subscribers = []  # dictionary to store subscribers interested in lottery results
        self._bot = bot

        '''
        for now subscribers will be the user that have voted
        '''

    async def get_unique_user(self, idLottery):  # put all users into subscribed list for now
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_URL}/all_users") as response:
                data = await response.json()
                for user in data:
                    self.subscribers.append(user["idUser"])
                return {'Got idUsers'}

    async def get_lottery_time_left(self, idLottery):
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_URL}/lottery?id={idLottery}") as response:
                data = await response.json()
                print(data)
                try:
                    createdTimeStr = data[0]['createdAt']
                    createdTime = datetime.strptime(createdTimeStr, '%Y-%m-%dT%H:%M:%S.%fZ')
                    createdTime = createdTime.timestamp()
                    givenTime = data[0]['givenTime']
                    return createdTime, givenTime
                except Exception as e:
                    print(e)
                    return 0, 0

    async def notify(self):
        print('Entering notification task')
        while True:
            await asyncio.sleep(5)
            idLottery = await client.get_id_lottery()

            if idLottery:
                print('found lottery, checking')
                createdTime, givenTime = await LotteryTimer.get_lottery_time_left(self, idLottery)
                timeLeft = int(createdTime + (givenTime * 60)) - int(datetime.now().timestamp())
                timeLeft = (timeLeft / 60)
                if timeLeft < 0:
                    print("Lottery have ended!!")
                    await client.stop_lottery()
                    await self.get_unique_user(idLottery)
                    winners = await client.get_winners(idLottery)
                    if not winners:
                        for idUser in self.subscribers:
                            print("Sent messages!")
                            await self._bot.send_message(chat_id=idUser, text=f"Time is up and No one have won the lottery!")

                    else:
                        for idUser in self.subscribers:
                            print("Sent messages!")
                            await self._bot.send_message(chat_id=idUser, text=f"Lottery have ended!\n"
                                                                              f"Winners are {winners}")


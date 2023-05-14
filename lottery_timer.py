import time
from datetime import datetime
import aiohttp
from os import environ
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware


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

    async def get_winners(self, idLottery):
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_URL}/lottery/winners?idLottery={idLottery}") as response:
                data = await response.json()
                print(data)
                if not data:
                    return False
                return data

    async def get_id_lottery(self) -> int:
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_URL}/lottery/running") as response:
                data = await response.json()
                if not data:
                    return 0
                return data

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


    async def get_unique_user(self, idLottery):  # put all users into subscribed list for now
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_URL}/all_users") as response:
                data = await response.json()
                for user in data:
                    self.subscribers.append(user["idUser"])
                return {'Got idUsers'}

    async def notify(self):
        print('Launched notification task')
        idLottery = await LotteryTimer.get_id_lottery(self)
        if not idLottery:
            return {'No lottery running'}
        createdTime, givenTime = await LotteryTimer.get_lottery_time_left(self, idLottery)
        while True:
            await asyncio.sleep(5)
            timeLeft = int(createdTime + (givenTime * 60)) - int(datetime.now().timestamp())
            timeLeft = (timeLeft / 60)
            if timeLeft < 0:
                print("Lottery have ended!!")
                await self.get_unique_user(idLottery)
                winners = await LotteryTimer.get_winners(self, idLottery)
                if not winners:
                    for idUser in self.subscribers:
                        print("Sent messages!")
                        await self._bot.send_message(chat_id=idUser, text=f"Time is up and No one have won the lottery!")
                    return
                else:
                    for idUser in self.subscribers:
                        print("Sent messages!")
                        await self._bot.send_message(chat_id=idUser, text=f"Lottery have ended!\n"
                                                                    f"Winners are {winners}")
                    return

            #     for subscriber in subscribers:
            #         subscriber.notify(lottery_id)
            #     del self.active_lotteries[lottery_id]
            #     del self.subscribers[lottery_id]
            #
            #
            #
            #
            #
            #
            #
            # for lottery_id, end_time in list(self.active_lotteries.items()):
            #     if now > end_time:
            #         # lottery has ended, notify subscribers and remove from active lotteries
            #         subscribers = self.subscribers.get(lottery_id, [])
            #         for subscriber in subscribers:
            #             subscriber.notify(lottery_id)
            #         del self.active_lotteries[lottery_id]
            #         del self.subscribers[lottery_id]
            # time.sleep(1)

    def add_lottery(self, lottery_id, end_time):
        self.active_lotteries[lottery_id] = end_time

    def add_subscriber(self, lottery_id, subscriber):
        self.subscribers.setdefault(lottery_id, []).append(subscriber)
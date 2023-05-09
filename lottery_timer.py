import threading
import time
from datetime import datetime
import aiohttp
from os import environ

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware

DATABASE_URL = "http://localhost:5000/api"
API_TOKEN = environ.get("BotApi")

bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

class LotteryTimer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.active_lotteries = {}  # dictionary to store active lotteries with their end times
        self.subscribers = {}  # dictionary to store subscribers interested in lottery results

        '''
        for now subscribers will be the user that have voted
        '''

    async def get_id_lottery(self):
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_URL}/lottery/running") as response:
                data = await response.json()
                print(data)
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
                except Exception as e:
                    print(e)

                return createdTime, givenTime

    async def run(self):
        idLottery = await LotteryTimer.get_id_lottery(self)
        createdTime, givenTime = await LotteryTimer.get_lottery_time_left(self, idLottery)
        while True:
            time.sleep(5)
            timeLeft = int(createdTime + (givenTime * 60)) - int(datetime.now().timestamp())
            timeLeft = (timeLeft / 60)
            if timeLeft < 0:
                print("Lottery have ended!!")

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
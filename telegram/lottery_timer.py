from datetime import datetime
import aiohttp
import asyncio

from aiogram import Bot
from backendClient import BackendClient
#from BitcoinWorker.client import BlockstreamClient
#import redis.asyncio as redis

client = BackendClient()
#bcClient = BlockstreamClient()

DATABASE_URL = "http://localhost:5000/api"
#myRedis = redis.Redis(host="localhost", port=6379, db=0)
#pubsub = myRedis.pubsub()


class LotteryTimer:
    def __init__(self, bot: Bot):
        super().__init__()
        self.active_lotteries = {}  # dictionary to store active lotteries with their end times
        self.subscribers = []  # dictionary to store subscribers interested in lottery results
        self._bot = bot

        '''
        for now subscribers will be the user that have voted
        '''

    async def get_unique_user(self, idLottery):
        data = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATABASE_URL}/users/allVote") as response:
                data = await response.json()
                print(data)
                for bet in data:
                    if bet["idLottery"] == idLottery:
                        self.subscribers.append(bet["idUser"])
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
            await asyncio.sleep(10)
            idLottery = await client.get_id_lottery()

            if idLottery:
                print('found lottery, checking')
                height = await client.get_height()
                lastHeight = 1 #await bcClient.get_last_height()
                if lastHeight > height:
                    print("stop allowing votes")
                    # stop people from voting, real function in the bot itself

                    if lastHeight > height+1:
                        currentHash = "curhash" #await bcClient.get_current_hash()
                        decimalId = int(currentHash, 16)
                        if decimalId % 2 == 0:
                            print('even')
                            await client.post_winning_choice('even')
                        else:
                            print('odd')
                            await client.post_winning_choice('odd')

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




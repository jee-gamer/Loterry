import asyncio

from celery import Celery
from celery.schedules import crontab
from os import environ
import redis
import json
import logging
from database import session
from database import Base, User, Bet, Lottery
import aiohttp

logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO
)

REDIS_HOST = environ.get("host", default="localhost")
REDIS_PORT = environ.get("port", default=6379)

app = Celery(broker="redis://localhost")

redis_service = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
# pubsub = redis_service.pubsub()
# pubsub.subscribe('bets')
# pubsub.subscribe('blocks')

bets_sub = redis_service.pubsub()
bets_sub.subscribe("bets")

blocks_sub = redis_service.pubsub()
blocks_sub.subscribe("blocks")

DATABASE_URL = "http://localhost:5000/api"
BTC_URL = "http://localhost:5001"

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        10.0, bets, name="checking for new vote messages in the queue"
    )
    sender.add_periodic_task(10.0, blocks, name="checking for new blocks in the queue")
    sender.add_periodic_task(10.0, notify_results, name="checking if the lottery ended")

    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        ads.s("Happy Mondays!"),
    )


def send_clicks(clickCount=99):
    logging.info(f"Sent clickCount {clickCount}  to redis ")
    # redis_service.publish("clickCount", clickCount)


@app.task
def bets():
    logging.info(f"running bets")

    for message in bets_sub.listen():
        channel = message["channel"].decode("utf-8")
        if message["type"] == "message" and channel == "bets":
            str_data = message["data"].decode()
            data = json.loads(str_data)
            if "idUser" in data.keys():
                try:
                    data["idUser"] = int(data["idUser"])
                    data["idLottery"] = int(data["idLottery"])
                    bet = data["userBet"]
                    if bet == "odd":
                        data["userBet"] = 1
                    elif bet == "even":
                        data["userBet"] = 2
                    else:
                        logging.error(f'unknown bet type {data["userBet"]}')
                    data["betSize"] = int(data["betSize"])
                except Exception as e:
                    logging.error(f"couldnt convert Bet data {e}")

                logging.info(
                    f'message {data["idUser"]} - {data["userBet"]} for lottery {data["idLottery"]}'
                )

                # 1 BTC per 1 click. 10 clicks = 10 BTC
                thisBet = Bet(data["uuid"], data["idUser"], data["idLottery"], data["userBet"], data["betSize"])
                session.add(thisBet)
                session.commit()

                thisMessage = json.dumps({data["idUser"]: "Submitted"})
                redis_service.publish(
                    "notify", thisMessage
                )

            else:
                logging.error(f"Invalid message data received {data}")


@app.task
def blocks():
    for message in blocks_sub.listen():
        channel = message["channel"].decode("utf-8")
        if message["type"] == "message" and channel == "blocks":
            str_data = message["data"].decode()
            data = json.loads(str_data)
            if "id" in data.keys():
                logging.info(f'Block processed {data["id"]}:{data["height"]}')
            else:
                logging.error(f"Invalid block data received {data}")


async def make_request(URL, method, endpoint, **kwargs):
    async with aiohttp.ClientSession() as session:
        url = f"{URL}{endpoint}"
        async with session.request(method, url, **kwargs) as response:
            data = await response.json()
            return data


async def get_unique_user(self, idLottery):
    data = None
    data = await make_request(DATABASE_URL, 'GET', "/users/allVote")
    if not data:
        return None
    for bet in data:
        if bet["idLottery"] == idLottery:
            self.subscribers.append(bet["idUser"])
    return {'Got idUsers'}


async def post_winning_choice(winningChoice):
    endpoint = f"/lottery/winningFruit"
    URL = "http://localhost:5000/api"
    data = {
        "winningChoice": winningChoice,
    }
    return await make_request(URL, 'POST', endpoint, json=data)


@app.task
async def notify_results():
    idLottery = await make_request(DATABASE_URL, "GET", "/lottery/running")
    if idLottery:
        print('found lottery, checking')
        lotteryHeight = await make_request(DATABASE_URL, "GET", "/lottery/height")
        lastHeight = await make_request(BTC_URL, "GET", "/tip")
        if lastHeight > lotteryHeight:
            print("stop allowing votes")
            # stop people from voting, real function in the bot itself

            if lastHeight > lotteryHeight + 1:
                currentHash = await make_request(BTC_URL, "GET", "/tip/hash")
                decimalId = int(currentHash, 16)
                if decimalId % 2 == 0:
                    print('even')
                    await post_winning_choice('even')
                else:
                    print('odd')
                    await post_winning_choice('odd')

                # await client.stop_lottery()  no such thing anymore

                data = await make_request(DATABASE_URL, 'GET', "/users/allVote")
                subscribers = []   # time to get all user that voted on this lottery
                if not data:
                    logging.info("No user voted on this lottery")
                    return None
                for bet in data:
                    if bet["idLottery"] == idLottery:
                        subscribers.append(bet["idUser"])

                winners = await make_request(DATABASE_URL, 'GET', f"/lottery/winners?idLottery={idLottery}")

                if not winners:
                    for idUser in subscribers:
                        thisMessage = json.dumps({idUser: f"Time is up and No one have won the lottery!"})
                        redis_service.publish(
                            "notify", thisMessage
                        )


                else:
                    for idUser in subscribers:
                        thisMessage = json.dumps({idUser: f"Lottery have ended!\n"
                                                          f"Winners are {winners}"})
                        redis_service.publish(
                            "notify", thisMessage
                        )



@app.task
def ads(arg):
    logging.info(f"Ad message {arg}")

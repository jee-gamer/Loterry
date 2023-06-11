from celery import Celery
from celery.schedules import crontab
from os import environ
import redis
import json
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)

REDIS_HOST = environ.get("host", default="localhost")
REDIS_PORT = environ.get("port", default=6379)

app = Celery(broker="redis://localhost")
DATABASE_URL = "http://localhost:5000/api"

redis_service = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
#pubsub = redis_service.pubsub()
#pubsub.subscribe('bets')
#pubsub.subscribe('blocks')

bets_sub = redis_service.pubsub()
bets_sub.subscribe('bets')

blocks_sub = redis_service.pubsub()
blocks_sub.subscribe('blocks')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, bets, name='checking for new vote messages in the queue')
    sender.add_periodic_task(10.0, blocks, name='checking for new blocks in the queue')

    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        ads.s('Happy Mondays!'),
    )


@app.task
def bets():
    for message in bets_sub.listen():
        channel = message['channel'].decode('utf-8')
        if message['type'] == 'message' and channel == 'bets':
            str_data = message['data'].decode()
            data = json.loads(str_data)
            if "idUser" in data.keys():
                logging.info(f'Message from user {data["idUser"]} - {data["userBet"]} for lottery {data["idLottery"]}')
            else:
                logging.error(f'Invalid message data received {data}')

    # users = session.query(User).all()
    # for user in users:
    #     logging.info(user.as_dict())
    #
    # lotteries = session.query(Lottery).filter(Lottery.running == 1)
    # for lottery in lotteries:
    #     logging.info(lottery.as_dict())


@app.task
def blocks():
    for message in blocks_sub.listen():
        channel = message['channel'].decode('utf-8')
        if message['type'] == 'message' and channel == 'blocks':
            str_data = message['data'].decode()
            data = json.loads(str_data)
            if "id" in data.keys():
                logging.info(f'Block processed {data["id"]}:{data["height"]}')
            else:
                logging.error(f'Invalid block data received {data}')


@app.task
def ads(arg):
    logging.info(f"Ad message {arg}")

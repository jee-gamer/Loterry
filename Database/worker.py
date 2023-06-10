from celery import Celery
from celery.schedules import crontab
from database import session, Base, User, Bet, Lottery
from os import environ
import redis
import json


REDIS_HOST = environ.get("host", default="0.0.0.0")
REDIS_PORT = environ.get("port", default=6379)

app = Celery(broker="redis://localhost")
DATABASE_URL = "http://localhost:5000/api"

redis_service = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
pubsub = redis_service.pubsub()
pubsub.subscribe('bets')
pubsub.subscribe('blocks')

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
    print("checking & processing bets")

    for message in pubsub.listen():
        if message['type'] == 'message':
            str_data = message['data'].decode()
            data = json.loads(str_data)
            print(data)
            #await client.post_bet(data["idUser"], data["idLottery"],
            #                      data["userBet"])
            print('Bet registered')

    users = session.query(User).all()
    for user in users:
        print(user.as_dict())

    lotteries = session.query(Lottery).filter(Lottery.running == 1)
    for lottery in lotteries:
        print(lottery.as_dict())


@app.task
def blocks():
    print("checking & processing blocks")
    for message in pubsub.listen():
        if message['type'] == 'message':
            str_data = message['data'].decode()
            data = json.loads(str_data)
            print(data)
            print('Block processed')

@app.task
def ads(arg):
    print(f"Ad message {arg}")

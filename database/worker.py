from celery import Celery
from celery.schedules import crontab
from os import environ
import redis
import json
import logging
from database import session
from database import Base, User, Bet, Lottery
from requests import request

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

invoice_sub = redis_service.pubsub()
invoice_sub.subscribe("invoice")

withdraw_sub = redis_service.pubsub()
withdraw_sub.subscribe("withdraw")

DATABASE_URL = "http://localhost:5000/api"


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        10.0, bets, name="checking for new vote messages in the queue"
    )
    sender.add_periodic_task(10.0, blocks, name="checking for new blocks in the queue")
    sender.add_periodic_task(10.0, notify_results, name="checking if the lottery ended")
    sender.add_periodic_task(10.0, check_invoice, name="checking if invoice is valid")
    sender.add_periodic_task(10.0, pay_invoice, name="checking if user balance and invoice is valid for paying")
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        ads.s("Happy Mondays!"),
    )


def send_clicks(clickCount=99):
    logging.info(f"Sent clickCount {clickCount}  to redis ")
    # redis_service.publish("clickCount", clickCount)


def make_request_btc(method, endpoint):
    response = request(method, f"http://localhost:5001{endpoint}")
    return response.json()


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

                user = session.query(User).filter(User.idUser == data["idUser"]).first()
                if user:
                    logging.info(
                        f'message {data["idUser"]} - {data["userBet"]} for lottery {data["idLottery"]}'
                    )

                    # 1 BTC per 1 click. 10 clicks = 10 BTC
                    thisBet = Bet(data["uuid"], data["idUser"], data["idLottery"], data["userBet"], data["betSize"])
                    session.add(thisBet)
                    session.commit()

                    # TODO: Update balance of the user
                    thisMessage = json.dumps({data["idUser"]: "Submitted"})
                    redis_service.publish(
                        "notify", thisMessage
                    )
                else:
                    logging.info(f'received bet from non-registered user {data["idUser"]}')
                    thisMessage = json.dumps({data["idUser"]: "Restart the bot (/start) to register user"})
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


@app.task
def notify_results():
    height = make_request_btc("GET", "/tip")
    lottery = session.query(Lottery).filter(Lottery.startedHeight == height).first()
    if lottery:
        print('found lottery, checking')
        lotteryHeight = lottery.startedHeight
        lastHeight = make_request_btc("GET", "/tip")
        if lastHeight > lotteryHeight:
            print("stop allowing votes")
            # stop people from voting, real function in the bot itself

            if lastHeight > lotteryHeight + 1:
                currentHash = make_request_btc("GET", "/tip/hash")
                decimalId = int(currentHash, 16)
                if decimalId % 2 == 0:
                    print('even')
                    lottery.winningFruit = 2
                    session.commit()
                else:
                    print('odd')
                    lottery.winningFruit = 1
                    session.commit()

                # await client.stop_lottery()  no such thing anymore
                data = [v.as_dict() for v in session.query(Bet).all()]
                subscribers = []   # time to get all user that voted on this lottery
                if not data:
                    logging.info("No user voted on this lottery")
                    return None
                for bet in data:
                    if bet["idLottery"] == lotteryHeight:
                        subscribers.append(bet["idUser"])

                #  getting winners
                winningFruit = lottery.winningFruit
                winningBet = session.query(Bet).filter(Bet.idLottery == lotteryHeight, Bet.userBet == winningFruit).all()
                winners = []
                if not winningBet:
                    logging.info("no winner")
                    return False
                for bet in winningBet:
                    if bet.user is None:  # if user is not registered (remove later)
                        name = f"UserId_{bet.idUser}"
                    else:
                        name = bet.user.alias  # this requires that the user of this bet have registered
                    print(name)
                    winners.append(name)
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


@app.task()
def check_invoice():  # add balance to user if got invoice
    for message in invoice_sub.listen():
        channel = message["channel"].decode("utf-8")
        if message["type"] == "message" and channel == "invoice":
            logging.info("got invoice msg")
            str_data = message["data"].decode()
            data = json.loads(str_data)
            if "userId" and "paymentHash" in data:
                invoiceStatus = request("GET", f"https://legend.lnbits.com/api/v1/payments/{data['paymentHash']}",
                               headers={"X-Api-Key": "a92d0ac5e4484910a35e9904903d3d53"})
                invoiceStatusData = json.loads(invoiceStatus.text)
                logging.info(invoiceStatusData)
            else:
                logging.info("Invalid userId or paymentHash")

            if invoiceStatusData["paid"]:
                user = session.query(User).filter(User.idUser == data["idUser"]).first()
                if user:
                    user.balance += invoiceStatusData['amount']
                else:
                    logging.info("User doesn't exist")


@app.task()
def pay_invoice():  # pay user that request withdraw and balance is valid
    for message in withdraw_sub.listen():
        channel = message["channel"].decode("utf-8")
        if message["type"] == "message" and channel == "withdraw":
            logging.info("got invoice msg")
            str_data = message["data"].decode()
            data = json.loads(str_data)
            if "userId" and "paymentHash" in data:
                invoiceStatus = request("GET", f"https://legend.lnbits.com/api/v1/payments/{data['paymentHash']}",
                               headers={"X-Api-Key": "a92d0ac5e4484910a35e9904903d3d53"})
                invoiceStatusData = json.loads(invoiceStatus.text)
                logging.info(invoiceStatusData)
            else:
                logging.info("Invalid userId or paymentHash")
            user = session.query(User).filter(User.idUser == data["idUser"]).first()  # the amount is big? still don't understand that
            if user and invoiceStatusData["amount"] <= user.balance:
                user.balance = user.balance - invoiceStatusData["amount"]
                withdrawInfo = {"out": True, "bolt11": data["paymentHash"]}
                request("POST", f"https://legend.lnbits.com/api/v1/payments", json=withdrawInfo,
                        headers={"X-Api-Key": "bd5d9c5422f2419ba0c94781d2fadf64"})  # admin key
            else:
                logging.info("User doesn't exist or user balance isn't enough")







@app.task
def ads(arg):
    logging.info(f"Ad message {arg}")

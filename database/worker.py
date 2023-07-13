from celery import Celery
from celery.schedules import crontab
from os import environ
import redis
import json
import logging
from database import session
from database import Base, User, Bet, Lottery
from sqlalchemy import desc

from requests import request
import time


logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO
)

REDIS_HOST = environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = environ.get("REDIS_PORT", default=6379)
DB_HOST = environ.get("DB_HOST", default="localhost")
DB_PORT = environ.get("DB_PORT", default=5000)
BTC_HOST = environ.get("BTC_HOST", default="localhost")
BTC_PORT = environ.get("BTC_PORT", default=5001)
DATABASE_URL = f"http://{DB_HOST}:{DB_PORT}/api"
LNBITS_API = environ.get("LNBITS_API")
LNBITS_ADMIN_API = environ.get("LNBITS_ADMIN_API")
USER_TASK_TIMEOUT=int(environ.get("USER_TASK_TIMEOUT", default=1))
BLOCK_TASK_TIMEOUT=int(environ.get("BLOCK_TASK_TIMEOUT", default=60))

app = Celery(broker=f"redis://{REDIS_HOST}:{REDIS_PORT}")

redis_service = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
# pubsub = redis_service.pubsub()
# pubsub.subscribe('bets')
# pubsub.subscribe('blocks')

bets_sub = redis_service.pubsub()
bets_sub.subscribe("tg/bets")
bets_sub.subscribe("discord/bets")

blocks_sub = redis_service.pubsub()
blocks_sub.subscribe("blocks")

invoice_sub = redis_service.pubsub()
invoice_sub.subscribe("tg/invoice")
invoice_sub.subscribe("discord/invoice")

withdraw_sub = redis_service.pubsub()
withdraw_sub.subscribe("tg/withdraw")
withdraw_sub.subscribe("discord/withdraw")


@app.on_after_configure.connect
def setup_tasks(sender, **kwargs):
    blocks.apply_async()
    bets.apply_async()
    # active one above
    check_invoice.apply_async()
    pay_invoice.apply_async()
    # seems like redis can run in background without taking space on the thread, so we have to put active one above


def make_request_btc(method, endpoint):
    response = request(method, f"http://{BTC_HOST}:{BTC_PORT}{endpoint}")
    return response.json()


@app.task
def bets():
    logging.info(f"running bets")

    for message in bets_sub.listen():
        logging.info("received user bet from redis")
        channel = message["channel"].decode("utf-8")
        if channel == "discord/bets":
            replyChannel = "discord/notify"
        else:
            replyChannel = "tg/notify"
        if message["type"] == "message":
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
                    logging.error(f"couldn't convert Bet data {e}")

                lastHeight = make_request_btc("GET", "/tip")

                if not data["idLottery"] == lastHeight:
                    thisMessage = json.dumps({data["idUser"]: "Time for voting is up!"})
                    redis_service.publish(
                        replyChannel, thisMessage
                    )
                    continue

                user = session.query(User).filter(User.idUser == data["idUser"]).first()
                if user:
                    # 1 BTC per 1 click. 10 clicks = 10 BTC
                    thisBet = Bet(data["uuid"], data["idUser"], data["idLottery"], data["userBet"], data["betSize"])
                    user.balance += data["betSize"]  # increase the balance for testing purpose
                    session.add(thisBet)
                    session.commit()
                    logging.info(
                        f'commited bet {data["userBet"]} for lottery {data["idLottery"]} in database. Now messaging {data["idUser"]}'
                    )
                    # TODO: Update balance of the user
                    thisMessage = json.dumps({data["idUser"]: "Submitted bet successfully"})
                    redis_service.publish(
                        replyChannel, thisMessage
                    )
                else:
                    logging.info(f'received bet from non-registered user {data["idUser"]}')
                    thisMessage = json.dumps({data["idUser"]: "Restart the bot (/start) to register user"})
                    redis_service.publish(
                        replyChannel, thisMessage
                    )
            else:
                logging.error(f"Invalid message data received {data}")


@app.task
def blocks():
    logging.info(f"running blocks consumer")

    for message in blocks_sub.listen():
        if message["type"] == "message":
            str_data = message["data"].decode()
            block = json.loads(str_data)
            if "id" in block.keys():
                logging.info(f'Block processed {block["id"]}:{block["height"]}')
                notify_results(block)
            else:
                logging.error(f"Invalid block data received {block}")


@app.task
def notify_results(block: dict):
    time.sleep(USER_TASK_TIMEOUT)
    lastHeight = block["height"]
    startedHeight = lastHeight - 2
    logging.info(f"Setting-up lotteries, current blockchain height {lastHeight}, to be determined {startedHeight}")
    lottery = session.query(Lottery).filter(Lottery.idLottery == startedHeight).first()
    # The first scenario: we have each State C, D, E

    if not lottery:
        logging.info(f"Lottery at height {startedHeight} is not found")
        return
    elif lottery.winningHash:
        logging.info(f"Results are already announced")
        return
    else:  # if it runs every time a new block comes then there's no need to check so much
        logging.info(f"Announce results for {startedHeight} at {lastHeight}")
        currentHash = block["id"]
        decimalId = int(currentHash, 16)
        lottery.winningHash = currentHash
        result = 0
        if decimalId % 2 == 0:
            result = 2
        else:
            result = 1
        session.commit()
        logging.info(f"Result {result} for {startedHeight}:{currentHash} commited into database")

        bets = session.query(Bet).filter(Bet.idLottery == startedHeight).all()

        if not bets: # one_or_none() -- an option
            logging.info("No user voted on this lottery")
            return

        tgSub = []   # time to get all user that voted on this lottery
        discordSub = []

        for bet in bets:
            if bet.idUser not in tgSub and bet.idUser not in discordSub:
                if len(str(bet.idUser)) == 18:
                    discordSub.append(bet.idUser)
                else:
                    tgSub.append(bet.idUser)

        #  getting winners
        winningBet = session.query(Bet).filter(Bet.idLottery == startedHeight, Bet.userBet == result).\
            group_by(Bet.idUser).all()  # group all bet with same user id together
        winners = []
        if not winningBet:
            logging.info(f"no winners, nobody tried this lottery {startedHeight}")
            return

        for bet in winningBet:
            if bet.user is None:  # if user is not registered (remove later)
                name = f"UserId_{bet.idUser}"
            else:
                name = bet.user.alias  # this requires that the user of this bet have registered
            logging.info(f"user {name} is winner in {startedHeight} / {result}")
            winners.append(name)

        if not winners:
            for idUser in tgSub:
                thisMessage = json.dumps({idUser: f"Time is up and No one have won the lottery!"})
                redis_service.publish(
                    "tg/notify", thisMessage
                )
            for idUser in discordSub:
                thisMessage = json.dumps({idUser: f"Time is up and No one have won the lottery!"})
                redis_service.publish(
                    "discord/notify", thisMessage
                )
        else:
            for idUser in tgSub:
                thisMessage = json.dumps({idUser: f"Lottery have ended!\n"
                                                  f"Winners are {winners}"})
                redis_service.publish(
                    "tg/notify", thisMessage
                )
            for idUser in discordSub:
                thisMessage = json.dumps({idUser: f"Lottery have ended!\n"
                                                  f"Winners are {winners}"})
                redis_service.publish(
                    "discord/notify", thisMessage
                )


@app.task()
def status_check(idUser, paymentHash, replyChannel):
    invoiceStatus = request("GET", f"https://legend.lnbits.com/api/v1/payments/{paymentHash}",
                            headers={"X-Api-Key": LNBITS_API})
    invoiceStatusData = json.loads(invoiceStatus.text)
    logging.info(f"This is the data we got {invoiceStatusData}")
    timeout = int(invoiceStatusData["details"]["expiry"])

    while True:
        timeNow = time.time()

        if timeNow >= timeout:
            logging.info("Timeout reached")
            msg = {idUser: f"The invoice is expired"}
            redis_service.publish(replyChannel, json.dumps(msg))
            return

        invoiceStatus = request("GET", f"https://legend.lnbits.com/api/v1/payments/{paymentHash}",
                                headers={"X-Api-Key": LNBITS_API})
        invoiceStatusData = json.loads(invoiceStatus.text)
        if invoiceStatusData["paid"]:
            user = session.query(User).filter(User.idUser == idUser).first()
            if user:
                depositedMoney = int(abs(invoiceStatusData['details']['amount'])/1000)  # the amount return negative when the payment is done for some reason
                user.balance += depositedMoney
                session.commit()
                balance = user.balance
                msg = {idUser: f"Deposit {depositedMoney} balance successfully \n"
                               f"Your balance is now {balance}"}
                redis_service.publish(replyChannel, json.dumps(msg))
            else:
                logging.info(f"User:{idUser} doesn't exist for some reason")  # it must exist in order to come to this point
            return
        time.sleep(BLOCK_TASK_TIMEOUT)


@app.task()
def check_invoice():  # add balance to user if got invoice
    for message in invoice_sub.listen():
        time.sleep(USER_TASK_TIMEOUT)
        channel = message["channel"].decode("utf-8")
        if channel == "discord/invoice":
            replyChannel = "discord/notify"
        else:
            replyChannel = "tg/notify"
        if message["type"] == "message":
            logging.info("got invoice msg")
            str_data = message["data"].decode()
            data = json.loads(str_data)
            if "idUser" and "paymentHash" in data:
                user = session.query(User).filter(User.idUser == data["idUser"]).first()
                if user:
                    status_check.apply_async((data["idUser"], data["paymentHash"], replyChannel), ignore_result=True)
                else:
                    msg = {data["idUser"]: f"User is not registered"}
                    redis_service.publish(replyChannel, json.dumps(msg))


@app.task()
def pay_invoice():  # pay user that request withdraw and balance is valid
    for message in withdraw_sub.listen():
        time.sleep(USER_TASK_TIMEOUT)
        channel = message["channel"].decode("utf-8")
        if channel == "discord/withdraw":
            replyChannel = "discord/notify"
        else:
            replyChannel = "tg/notify"
        if message["type"] == "message":
            logging.info("got invoice msg")
            str_data = message["data"].decode()
            data = json.loads(str_data)
            logging.info(data)
            user = session.query(User).filter(User.idUser == data["idUser"]).first() #  ( I guess it doesn't update when I overwrite it in db brower but it works anyway)
            if not user:
                logging.info("User doesn't exist")
                msg = {user.idUser: f"User is not registered"}
                redis_service.publish(replyChannel, json.dumps(msg))
                continue
            withdrawInfo = {
                "data": data["bolt11"]
            }
            response = request("POST", f"https://legend.lnbits.com/api/v1/payments/decode", json=withdrawInfo,
                               headers={"X-Api-Key": LNBITS_API})
            logging.info("SUCCESS OR NAH")
            decodeData = response.json()
            if response.status_code == 200:
                logging.info(f"decoded invoice {decodeData}")
                amount = decodeData["amount_msat"]/1000
            else:
                logging.info(f"Error decoding invoice from request {data}")
                msg = {user.idUser: f"Error decoding invoice"}
                redis_service.publish(replyChannel, json.dumps(msg))
                continue
            if amount <= user.balance:
                logging.info(f"enough balance, proceed with payment, withdrawing {amount}")
                user.balance = user.balance - amount
                session.commit()
                withdrawInfo = {"out": True, "bolt11": data["bolt11"]}
                request("POST", f"https://legend.lnbits.com/api/v1/payments", json=withdrawInfo,
                        headers={"X-Api-Key": LNBITS_ADMIN_API})  # admin key
                msg = {user.idUser: f"withdraw {amount} sats complete"}
                redis_service.publish(replyChannel, json.dumps(msg))
            else:
                logging.info(f"User balance isn't enough, Balance is {user.balance}, trying to withdraw {amount}")
                msg = {user.idUser: f"User balance isn't enough"}
                redis_service.publish(replyChannel, json.dumps(msg))


@app.task()
def ads(arg):
    logging.info(f"Ad message {arg}")

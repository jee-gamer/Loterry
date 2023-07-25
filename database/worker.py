import configparser
from os.path import isfile

from celery import Celery
from celery.schedules import crontab
from os import environ
import redis
import json
import logging
from database import session
from database import Base, User, Bet, Chat, Lottery
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
USER_TASK_TIMEOUT = int(environ.get("USER_TASK_TIMEOUT", default=1))
BLOCK_TASK_TIMEOUT = int(environ.get("BLOCK_TASK_TIMEOUT", default=60))
FEE = int(environ.get("FEE", default=1))

config = configparser.ConfigParser()
if isfile('/run/secrets/lnbits.ini'):
    config.read_file(open('/run/secrets/lnbits.ini'))
else:
    config.read_file(open('./cache/secrets/lnbits.ini'))

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

chat_sub = redis_service.pubsub()
chat_sub.subscribe("chat")

invoice_sub = redis_service.pubsub()
invoice_sub.subscribe("tg/invoice")
invoice_sub.subscribe("discord/invoice")

withdraw_sub = redis_service.pubsub()
withdraw_sub.subscribe("tg/withdraw")
withdraw_sub.subscribe("discord/withdraw")

payments_sub = redis_service.pubsub()
payments_sub.subscribe("tg/invoice")
payments_sub.subscribe("discord/invoice")
payments_sub.subscribe("tg/withdraw")
payments_sub.subscribe("discord/withdraw")


@app.on_after_configure.connect
def setup_tasks(sender, **kwargs):
    blocks.apply_async()
    bets.apply_async()
    # get_message.apply_async()
    # active one above
    payments.apply_async()
    # check_invoice.apply_async()
    # pay_invoice.apply_async()
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
            bet_id = data["uuid"]
            id = 0
            bet = "None"
            lottery = 0
            if "idUser" in data.keys():
                try:
                    id = int(data["idUser"])
                    lottery = int(data["idLottery"])
                    bet = data["userBet"]
                    if bet == "odd":
                        bet = 1
                    elif bet == "even":
                        bet = 2
                    else:
                        logging.error(f"unknown bet type {bet}")
                except Exception as e:
                    logging.error(f"couldn't convert Bet data {e}")
                    redis_service.publish(
                        replyChannel, f"Failed to submit {bet} from user"
                    )
                    continue

                lastHeight = make_request_btc("GET", "/tip")

                if not lottery == lastHeight:
                    thisMessage = json.dumps({id: "Time for voting is up\!"})
                    redis_service.publish(replyChannel, thisMessage)
                    continue

                user = session.query(User).filter(User.idUser == id).first()
                if user:
                    new_balance = user.balance - user.betSize
                    if new_balance > 0:
                        # 1 BTC per 1 click. 10 clicks = 10 BTC
                        thisBet = Bet(bet_id, id, lottery, bet, user.betSize)
                        session.add(thisBet)
                        session.commit()
                        logging.info(
                            f"commited bet {bet} for lottery {lottery} in database. Now messaging {id}"
                        )
                        logging.info(
                            f"committing balance {new_balance} for {id}. Previous {user.balance}"
                        )
                        user.balance = (
                            new_balance  # update user balance
                        )
                        session.add(user)
                        session.commit()
                        # TODO: Update balance of the user
                        thisMessage = json.dumps(
                            {
                                id: f"Submitted {'odd' if bet == 1 else 'even'} for {lottery}"
                            }
                        )
                    else:
                        thisMessage = json.dumps(
                            {id: "Not enough balance\. Please, /deposit some sats"}
                        )
                else:
                    logging.error(f"received bet from non-registered user {id}")
                    thisMessage = json.dumps(
                        {id: "Restart the bot (/start) to register user"}
                    )

                redis_service.publish(replyChannel, thisMessage)
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
                freeze_message(block)
            else:
                logging.error(f"Invalid block data received {block}")


def freeze_message(block):
    lastHeight = block["height"]
    startedHeight = lastHeight - 1
    allChat = session.query(Chat).filter(Chat.idLottery == startedHeight).all()
    if not allChat:
        logging.info("There's no chat with freezing lottery")
        return
    for chat in allChat:
        idChat, idMessage = chat.idChat.split(":")
        thisMessage = json.dumps(
            {
                "idChat": idChat,
                "idMessage": idMessage,
                "idLottery": startedHeight,
                "height": lastHeight,
            }
        )
        redis_service.publish("freeze", thisMessage)
    session.query(Chat).filter(
        Chat.idLottery == startedHeight
    ).delete()  # delete msg because it's already been used
    session.commit()


def notify_results(block: dict):
    time.sleep(USER_TASK_TIMEOUT)
    lastHeight = block["height"]
    startedHeight = lastHeight - 2
    logging.info(
        f"Setting-up lotteries, current blockchain height {lastHeight}, to be determined {startedHeight}"
    )
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
        session.commit()
        if decimalId % 2 == 0:
            result = 2
        else:
            result = 1
        logging.info(
            f"Result {result} for {startedHeight}:{currentHash} commited into database"
        )

        shortHash = "`" + currentHash[:6] + "\-" + currentHash[-6:] + "`" #escape - for MarkdownV2 formatting

        bets = session.query(Bet).filter(Bet.idLottery == startedHeight).all()

        if not bets:  # one_or_none() -- an option
            logging.info("No user voted on this lottery")
            return

        tgSub = []  # time to get all user that voted on this lottery
        discordSub = []
        winners = []
        losers = []

        for bet in bets:
            if bet.idUser not in tgSub and bet.idUser not in discordSub:
                if len(str(bet.idUser)) == 18:
                    discordSub.append(bet.idUser)
                else:
                    tgSub.append(bet.idUser)
                if bet.user is None:  # if user is not registered (remove later)
                    name = f"UserId_{bet.idUser}"
                else:
                    name = bet.user.alias
                if bet.userBet == result:
                    winners.append(name)
                else:
                    losers.append(name)

            if bet.userBet == result:
                if bet.betSize * 2 - FEE <= 0:
                    bet.user.balance += int(bet.betSize * 1.5)
                else:
                    bet.user.balance += bet.betSize * 2 - FEE
        session.commit()

        if not winners and not losers:
            logging.info(f"nobody tried this lottery {startedHeight}")
            return
        elif not winners:
            for idUser in tgSub:
                thisMessage = json.dumps(
                    {idUser: f"Time is up and No one have won the lottery\!"}
                )
                redis_service.publish("tg/notify", thisMessage)
            for idUser in discordSub:
                thisMessage = json.dumps(
                    {idUser: f"Time is up and No one have won the lottery\!"}
                )
                redis_service.publish("discord/notify", thisMessage)
        else:
            for idUser in tgSub:
                thisMessage = json.dumps(
                    {
                        idUser: f"Lottery have ended\!\n"
                        f"This lottery hash: {shortHash}\n"
                        f"Winners are {', '.join(winners)}\n"
                        f"Losers are {', '.join(losers)}"
                    }
                )
                redis_service.publish("tg/notify", thisMessage)
            for idUser in discordSub:
                thisMessage = json.dumps(
                    {
                        idUser: f"Lottery have ended\!\n"
                        f"This lottery hash: {shortHash}\n"
                        f"Winners are {', '.join(winners)}\n"
                        f"Losers are {', '.join(losers)}"
                    }
                )
                redis_service.publish("discord/notify", thisMessage)


@app.task()
def status_check(idUser, paymentHash, replyChannel, amount):
    time_start = time.time()
    logging.info(f"checking status for {paymentHash}, user {idUser} since {time_start}")
    while time_start + 300 > time.time():
        response = request(
            "GET",
            f"https://legend.lnbits.com/api/v1/payments/{paymentHash}",
            headers={"X-Api-Key": LNBITS_API},
        )

        if response.status_code != 200:
            msg = {
                idUser: f"Couldnt obtain payment status\. Please, try again later"
            }
            redis_service.publish(replyChannel, json.dumps(msg))
            return

        payment = response.json()
        logging.info(f"payment {paymentHash} paid - {payment['paid']}")

        if payment["paid"]:
            user = session.query(User).filter(User.idUser == idUser).first()
            if user:
                user.balance += int(amount) # positive - deposit; negative - withdrawal
                session.commit()
                msg = {
                    idUser: f"Your balance updated: {user.balance}"
                }
                redis_service.publish(replyChannel, json.dumps(msg))
            else:
                logging.error(
                    f"User:{idUser} doesn't exist for some reason"
                )  # it must exist in order to come to this point
            return
        time.sleep(USER_TASK_TIMEOUT)

    logging.info(f"timeout for {paymentHash}")
    msg = {idUser: f"Expired\. Please try again later"}
    redis_service.publish(replyChannel, json.dumps(msg))
    return


@app.task()
def payments():  # add balance to user if got invoice
    for message in payments_sub.listen():
        time.sleep(USER_TASK_TIMEOUT)
        channel = message["channel"].decode("utf-8")
        if channel == "discord/invoice":
            replyChannel = "discord/notify"
        else:
            replyChannel = "tg/notify"
        if message["type"] == "message" and "invoice" in channel:
            str_data = message["data"].decode()
            data = json.loads(str_data)
            logging.info(f"received invoice request {data}")
            if "idUser" and "paymentHash" in data:
                logging.info(
                    f'received invoice with hash {data["paymentHash"]} for {data["idUser"]}'
                )
                user = session.query(User).filter(User.idUser == data["idUser"]).first()
                if user:
                    status_check(data["idUser"], data["paymentHash"], replyChannel, data["amount"])
                else:
                    msg = {data["idUser"]: f"User is not registered"}
                    redis_service.publish(replyChannel, json.dumps(msg))
        if message["type"] == "message" and "withdraw" in channel:
            str_data = message["data"].decode()
            data = json.loads(str_data)
            logging.info(f"received withdrawal request {data}")
            user = (
                session.query(User).filter(User.idUser == data["idUser"]).first()
            )  #  ( I guess it doesn't update when I overwrite it in db brower but it works anyway)
            if not user:
                logging.info("User doesn't exist")
                msg = {user.idUser: f"User is not registered"}
                redis_service.publish(replyChannel, json.dumps(msg))
                continue
            withdrawInfo = {"data": data["bolt11"]}
            response = request(
                "POST",
                f"https://legend.lnbits.com/api/v1/payments/decode",
                json=withdrawInfo,
                headers={"X-Api-Key": LNBITS_API},
            )
            decodeData = response.json()
            if response.status_code == 200:
                amount = decodeData["amount_msat"] / 1000
                logging.info(
                    f"decoded invoice {decodeData['payment_hash']} for {amount}"
                )
            else:
                logging.error(f"error decoding invoice from request {data}")
                msg = {user.idUser: f"Error decoding invoice"}
                redis_service.publish(replyChannel, json.dumps(msg))
                continue
            if amount <= user.balance:
                logging.info(
                    f"enough balance, proceed with payment, withdrawing {amount}"
                )
                withdrawInfo = {"out": True, "bolt11": data["bolt11"]}
                response = request(
                    "POST",
                    f"https://legend.lnbits.com/api/v1/payments",
                    json=withdrawInfo,
                    headers={"X-Api-Key": config['KEYS']['ADMIN']},
                )
                if response.status_code == 201:
                    payment = response.json()
                    logging.info(f"received {response.status_code} from LnBits for payment {payment['payment_hash']}")
                    msg = {user.idUser: f"Withdraw submitted `{payment['payment_hash']}`"}
                    redis_service.publish(replyChannel, json.dumps(msg))
                    status_check(data["idUser"], decodeData["payment_hash"], replyChannel, -amount)
                else:
                    logging.error(f"received {response.status_code}. Dump {response.text}")
                    msg = {user.idUser: f"Withdraw failed"}
                    redis_service.publish(replyChannel, json.dumps(msg))
            else:
                logging.info(
                    f"not enough money, balance is {user.balance}, trying to withdraw {amount}"
                )
                msg = {user.idUser: f"User balance isn't enough"}
                redis_service.publish(replyChannel, json.dumps(msg))

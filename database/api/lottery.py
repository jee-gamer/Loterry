from database import session
from database import Base, User, Bet, Lottery
from flask import request, jsonify
import logging
from datetime import datetime
from sqlalchemy import func, desc
import aiohttp

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)

BTC_URL = "http://localhost:5001"


async def make_request(method, endpoint, **kwargs):
    async with aiohttp.ClientSession() as session:
        url = f"{BTC_URL}{endpoint}"
        async with session.request(method, url, **kwargs) as response:
            data = await response.json()
            return data


def get_lottery(id):
    lottery = session.query(Lottery).filter(Lottery.idLottery == id).first()
    if not lottery:
        return jsonify({'message': 'Lottery not found'}), 404
    return jsonify([session.query(Lottery).filter(Lottery.idLottery == id).one().as_dict()])


async def start_lottery():

    maxId = session.query(func.max(Lottery.idLottery)).scalar()
    if not maxId:
        maxId = 0
    idLottery = maxId + 1

    # height = await bcClient.get_last_height()
    height = 1
    if not height:
        return jsonify({'message': 'Cant get block height'})
    lottery = Lottery(idLottery, height)
    session.add(lottery)
    session.commit()
    return jsonify([session.query(Lottery).filter(Lottery.startedHeight == height).first().as_dict()])
    # {'message': 'lottery started'}


async def post_winning_choice():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    data = request.get_json()
    if lottery:
        lottery.winningFruit = data["winningChoice"]
        session.commit()
        return jsonify([session.query(Lottery).filter(Lottery.running == 1).first().as_dict()])
    return {'message': 'Lottery not found'}
    # {'message': 'lottery started'}


def get_time_left():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if not lottery:
        return {'message': 'Lottery not found'}

    timeLeftUnix = lottery.createdAt
    givenTime = lottery.givenTime
    timeLeft = int(timeLeftUnix.timestamp() + (givenTime * 60)) - int(datetime.now().timestamp())
    timeLeft = (timeLeft / 60)

    return jsonify(timeLeft)


def get_height():
    lottery = session.query(Lottery).order_by(desc(Lottery.idLottery)).first()
    if not lottery:
        return {'message': 'Lottery not found'}

    height = lottery.startedHeight
    logging.info(f"height{height}")
    return jsonify(height)


def get_winning_fruit(idLottery):
    lottery = session.query(Lottery).filter(Lottery.idLottery == idLottery).first()
    if not lottery:
        return {'message': 'Lottery not found'}

    winningFruit = lottery.winningFruit
    return jsonify(winningFruit)


def get_winners(idLottery):
    lottery = session.query(Lottery).filter(Lottery.idLottery == idLottery).first()
    if not lottery:
        return False  # {'message': 'Lottery not found'}

    winningFruit = lottery.winningFruit
    winner = []
    winningBet = session.query(Bet).filter(Bet.idLottery == idLottery, Bet.userBet == winningFruit).all()
    if not winningBet:
        print("no winner")
        return False  # {'message': 'No winner'}
    winner = []

    for bet in winningBet:
        if bet.user is None:
            name = f"UserId_{bet.idUser}"
        else:
            name = bet.user.alias  # this requires that the user of this bet have registered
        print(name)
        winner.append(name)

    return jsonify(winner)


async def get_running_lottery():

    endpoint = f"/tip"
    tip_value = await make_request('GET', endpoint)

    lottery = session.query(Lottery).filter(Lottery.startedHeight == tip_value).first()
    lottery2 = session.query(Lottery).filter(Lottery.startedHeight + 1 == tip_value).first()
    if not lottery and not lottery2:
        return None
        #  {'message': 'No lottery is running'}

    lotteryId = lottery.idLottery
    return jsonify(lotteryId)


def stop_lottery():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if not lottery:
        return {'message': 'No lottery is running'}
    lottery.running = 0
    session.commit()
    return {'message': 'Stopped a running lottery'}

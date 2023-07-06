from database import session
from database import Base, User, Bet, Lottery
from flask import request, jsonify
import logging
from datetime import datetime
from sqlalchemy import func, desc
from requests import request
from os import environ

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)

BTC_HOST = environ.get("BTC_HOST", default="localhost")
BTC_PORT = environ.get("BTC_PORT", default=5001)


def make_request(method, endpoint):
    response = request(method, f"http://{BTC_HOST}:{BTC_PORT}{endpoint}")
    return response.json()


def get_lottery(id: int):
    # Sanity check
    if id < 794881:
        logging.error(f"attempt to create invalid lottery {id}")
        return jsonify(None)
    lottery = session.query(Lottery).filter(Lottery.startedHeight == id).first()
    if not lottery:
        return jsonify(None)
        #return jsonify({'message': 'Lottery not found'}), 404
    return jsonify([session.query(Lottery).filter(Lottery.startedHeight == id).one().as_dict()])


def start_lottery():

    maxId = session.query(func.max(Lottery.idLottery)).scalar()
    if not maxId:
        maxId = 0
    idLottery = maxId + 1

    endpoint = f"/tip"
    height = make_request('GET', endpoint)

    if not height:
        return jsonify({'message': 'Cant get block height'})
    lottery = Lottery(idLottery, height)
    session.add(lottery)
    session.commit()
    return jsonify([session.query(Lottery).filter(Lottery.startedHeight == height).first().as_dict()])
    # {'message': 'lottery started'}


def post_winning_choice():
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
    logging.info(f"height {height}")
    return jsonify(height)


def get_winning_fruit(idLottery):
    lottery = session.query(Lottery).filter(Lottery.idLottery == idLottery).first()
    if not lottery:
        return {'message': 'Lottery not found'}

    winningFruit = lottery.winningFruit
    return jsonify(winningFruit)


def get_winners(idLottery):
    lottery = session.query(Lottery).filter(Lottery.startedHeight == idLottery).first()
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


def stop_lottery():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if not lottery:
        return {'message': 'No lottery is running'}
    lottery.running = 0
    session.commit()
    return {'message': 'Stopped a running lottery'}

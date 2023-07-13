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
    lottery = session.query(Lottery).filter(Lottery.idLottery == id).first()
    if not lottery:
        return jsonify(None)
        #return jsonify({'message': 'Lottery not found'}), 404
    return jsonify([session.query(Lottery).filter(Lottery.idLottery == id).one().as_dict()])


def start_lottery():
    height = make_request('GET', "/tip")
    if not height:
        return jsonify({'message': 'Cant get block height'})
    # to avoid error on add
    lottery = session.query(Lottery).filter(Lottery.idLottery == height).first()
    if lottery:
        # State B
        return jsonify({"height": height})
    # State A - the Lottery will be created and transits to State B
    lottery = Lottery(height)
    session.add(lottery)
    session.commit()
    return jsonify({"height": height})


def post_winning_hash(idLottery):
    lottery = session.query(Lottery).filter(Lottery.idLottery == idLottery).first()
    data = request.get_json()
    if lottery and not lottery.winningHash:
        # the state should be either started or frozen
        lottery.winningHash = data["winningHash"]
        session.commit()
        return jsonify([session.query(Lottery).filter(Lottery.idLottery == idLottery).first().as_dict()])
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

    height = lottery.idLottery
    logging.info(f"height {height}")
    return jsonify(height)


def get_winning_hash(idLottery):
    lottery = session.query(Lottery).filter(Lottery.idLottery == idLottery).first()
    if not lottery:
        return {'message': 'Lottery not found'}

    winningHash = lottery.winningHash
    return jsonify(winningHash)


def get_winners(idLottery):  # get winner that is already registered/processed
    lottery = session.query(Lottery).filter(Lottery.idLottery == idLottery).first()
    if not lottery:
        return False  # {'message': 'Lottery not found'}

    winningHash = lottery.winningHash
    decimalId = int(winningHash, 16)
    result = 0
    if decimalId % 2 == 0:
        logging.info(f"result EVEN for {idLottery}")
        result = 2
    else:
        logging.info(f"result ODD for {idLottery}")
        result = 1
    winner = []
    winningBet = session.query(Bet).filter(Bet.idLottery == idLottery, Bet.userBet == result). \
        group_by(Bet.idUser).all()  # group all bet with same user id together
    winners = []
    if not winningBet:
        logging.info(f"no winners, nobody tried this lottery {idLottery}")

    for bet in winningBet:
        if bet.user is None:  # if user is not registered (remove later)
            name = f"UserId_{bet.idUser}"
        else:
            name = bet.user.alias  # this requires that the user of this bet have registered
        logging.info(f"user {name} is winner in {lottery.idLottery} / {result}")
        winners.append(name)

    return jsonify(winner)


def stop_lottery():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if not lottery:
        return {'message': 'No lottery is running'}
    lottery.running = 0
    session.commit()
    return {'message': 'Stopped a running lottery'}


def reset_lottery(id: int):
    lottery = session.query(Lottery).filter(Lottery.idLottery == id).first()
    if not lottery:
        return jsonify(None)
    lottery.winningHash = ""
    session.commit()
    return jsonify({"result": "ok", 'message': 'removed'})

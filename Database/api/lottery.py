from Database.database import session, Base, User, Bet, Lottery
from flask import request, jsonify
import logging
from datetime import datetime
from sqlalchemy import func

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


def get_lottery(id):
    lottery = session.query(Lottery).filter(Lottery.idLottery == id).first()
    if not lottery:
        return jsonify({'message': 'Lottery not found'}), 404
    return jsonify([session.query(Lottery).filter(Lottery.idLottery == id).one().as_dict()]), 200


def start_lottery():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if lottery:
        return {'message': 'There is already an active lottery'}

    maxId = session.query(func.max(Lottery.idLottery)).scalar()
    if not maxId:
        maxId = 0
    idLottery = maxId + 1
    lottery = Lottery(idLottery)
    session.add(lottery)
    session.commit()
    return {'message': 'lottery started'}


def get_time_left():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if not lottery:
        return {'message': 'Lottery not found'}

    timeLeftUnix = lottery.createdAt
    givenTime = lottery.givenTime
    timeLeft = int(timeLeftUnix.timestamp() + (givenTime * 60)) - int(datetime.now().timestamp())
    timeLeft = (timeLeft / 60)

    return jsonify(timeLeft)


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


def get_running_lottery():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if not lottery:
        return {'message': 'No lottery is running'}

    lotteryId = lottery.idLottery
    return jsonify(lotteryId)


def stop_lottery():
    lottery = session.query(Lottery).filter(Lottery.running == 1).first()
    if not lottery:
        return {'message': 'No lottery is running'}
    lottery.running = 0
    session.commit()
    return {'message': 'Stopped a running lottery'}


def reset_everything():  # guess this thing only reset the internet
    session.query(User).delete()
    session.query(Lottery).delete()
    session.query(Bet).delete()
    return {'message': 'GONEEEEEEEE'}
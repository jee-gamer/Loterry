import requests

from Database.database import session, Base, User, Bet, Lottery
from flask import request, jsonify
from requests import Response
import json
from hashlib import sha1
import logging
from datetime import datetime
from sqlalchemy import func

#  ahah broken database path
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


def get_user(id) -> dict:
    user = session.query(User).filter(User.idUser == id).first()
    if user:
        return jsonify(user.as_dict())
    return jsonify(f"user not found")


def post_user() -> dict:
    data = request.get_json()
    print(data)

    user = session.query(User).filter(User.idUser == data["id"]).first()
    if user:
        return {'message': 'User with same id already exist'}

    user = User(data["id"], data["alias"], data["firstName"], data["lastName"])
    session.add(user)
    session.commit()
    return {'message': 'data received'}


def get_user_vote(id):
    bet = session.query(Bet).filter(Bet.idUser == id).all()
    if not bet:
        return {'message': 'User vote not found'}
    return jsonify([v.as_dict() for v in session.query(Bet).filter(User.idUser == id).all()])


def post_user_vote() -> dict:  # need to check if lottery exist or working!
    data = request.get_json()
    print(data)

    sameBet = session.query(Bet).filter(Bet.idUser == data["idUser"], Bet.idLottery == data["idLottery"], Bet.userBet == data["userBet"]).all()
    if sameBet:
        return {'message': 'This bet is a Duplicate'}

    lottery = session.query(Lottery).filter(Lottery.idLottery == data["idLottery"]).first()
    if not lottery:
        return {'message': 'Lottery not found'}

    maxId = session.query(func.max(Bet.idBet)).scalar()
    if not maxId:
        maxId = 0
    idBet = maxId + 1

    bet = Bet(idBet, data["idUser"], data["idLottery"], data["userBet"])
    session.add(bet)
    session.commit()
    return {'message': 'data received'}


def get_lottery(id):
    lottery = session.query(Lottery).filter(Lottery.idLottery == id).first()
    if not lottery:
        return {'message': 'Lottery not found'}
    return jsonify([session.query(Lottery).filter(Lottery.idLottery == id).one().as_dict()])


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


def reset_everything():  # guess this thing only reset the internet
    session.query(User).delete()
    session.query(Lottery).delete()
    session.query(Bet).delete()
    return {'message': 'GONEEEEEEEE'}

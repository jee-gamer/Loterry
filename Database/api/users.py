import requests

from Database.database import session, Base, User, Bet, Lottery
from flask import request, jsonify
from requests import Response
import json
from hashlib import sha1
import logging
import datetime
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


def post_user_vote() -> dict:
    data = request.get_json()
    print(data)

    sameBet = session.query(Bet).filter(Bet.idUser == data["idUser"], Bet.idLottery == data["idLottery"], Bet.userBet == data["userBet"]).all()
    if sameBet:
        return {'message': 'This bet is a Duplicate'}
    maxId = session.query(func.max(Bet.idBet)).scalar()
    if not maxId:
        maxId = 0
    idBet = maxId + 1

    bet = Bet(idBet, data["idUser"], data["idLottery"], data["userBet"])
    session.add(bet)
    session.commit()
    return {'message': 'data received'}


def get_lottery(id):
    lottery = session.query(Lottery).filter(Lottery.idLottery == id).all()
    if not lottery:
        return {'message': 'Lottery not found'}
    return jsonify([v.as_dict() for v in session.query(Lottery).filter(Lottery.idLottery == id).all()])


def start_lottery():
    maxId = session.query(func.max(Lottery.idLottery)).scalar()
    if not maxId:
        maxId = 0
    idLottery = maxId + 1
    lottery = Lottery(idLottery)
    session.add(lottery)
    session.commit()
    return {'message': 'data received'}
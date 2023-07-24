import requests
from database import session
from database import Base, User, Bet, Lottery
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


def get_users() -> dict:
    users = session.query(User).all()
    user_dicts = []
    for user in users:
        user_dicts.append(user.as_dict())
    return jsonify(user_dicts)


def post_user() -> dict:
    data = request.get_json() or {'result': 'ok', 'message': 'Empty User data'}
    user = session.query(User).filter(User.idUser == data["id"]).first()
    if user:
        return {'result': 'error', 'message': 'User with same id already exist'}
    id = data.get("id")
    alias = data.get("alias") or ""
    first_name = data.get("firstName") or ""
    last_name = data.get("lastName") or ""
    logging.info("adding new user") or ""
    user = User(id, alias, first_name, last_name)
    session.add(user)
    session.commit()
    return {'result': 'ok', 'message': 'User registered'}


def get_user_vote(id):
    bet = session.query(Bet).filter(Bet.idUser == id).all()
    if not bet:
        return {'result': 'ok', 'message': 'User vote not found'}
    return jsonify([v.as_dict() for v in session.query(Bet).filter(User.idUser == id).all()])


def get_users_vote():
    bet = session.query(Bet).all()
    if not bet:
        return {'result': 'ok', 'message': 'User vote not found'}
    return jsonify([v.as_dict() for v in bet])


def get_balance(id):
    user = session.query(User).filter(User.idUser == id).first()
    if not user:
        return {'result': 'ok', 'message': 'User not found'}
    return jsonify(user.balance)


def post_user_vote() -> dict:  # need to check if lottery exist or working!
    data = request.get_json()
    print(data)

    sameBet = session.query(Bet).filter(Bet.idUser == data["idUser"], Bet.idLottery == data["idLottery"]).all()
    if sameBet:
        return {'result': 'ok', 'message': 'Already voted on this lottery'}

    lottery = session.query(Lottery).filter(Lottery.idLottery == data["idLottery"]).first()
    if not lottery:
        return {'result': 'ok', 'message': 'Lottery not found'}

    # user = session.query(User).filter(User.idUser == data["idUser"]).first()
    # if not user:
    #     post_user()

    maxId = session.query(func.max(Bet.idBet)).scalar()
    if not maxId:
        maxId = 0
    idBet = maxId + 1

    bet = Bet(idBet, data["idUser"], data["idLottery"], data["userBet"])
    session.add(bet)
    session.commit()
    return {'result': 'ok', 'message': 'data received'}


def post_bet_setting(id, betSize):
    user = session.query(User).filter(User.idUser == id).first()
    if not user:
        return {'result': 'ok', 'message': 'User vote not found'}
    user.betSize = betSize
    session.commit()
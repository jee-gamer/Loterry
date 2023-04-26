import requests

from Database.database import session, Base, User, Bet, Lottery
from flask import request, jsonify
from requests import Response
import json
from hashlib import sha1
import logging
import datetime


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


def get_users(id) -> dict:
    if id > 11:
        return jsonify({'error': 'User doesnt exit'}), 400
    return jsonify([u.alias for u in session.query(User)])


def post_users() -> dict:
    data = request.get_json()
    print(data)
    return {'message': 'data received'}
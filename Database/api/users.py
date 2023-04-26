from Database.database import session, Base, User, Bet, Lottery
from flask import request, jsonify
import json
from hashlib import sha1
import logging
import datetime


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


def get_users(id) -> dict:
    return jsonify([u.alias for u in session.query(User)])


def post_users() -> dict:
    if request.method == 'POST' and request.is_json:
        return {'error': 'wrong value submitted'}
    return {'error': 'wrong request'}
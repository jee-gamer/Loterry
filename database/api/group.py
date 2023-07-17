import requests
from database import session
from database import Base, User, Bet, Lottery, Group
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


def post_group(idGroup, idLottery, idChat):
    group = session.query(Group).filter(User.idGroup == idGroup).first()
    if group:
        logging.info("Trying to post duplicate group")
        return {'message': 'Trying to post duplicate group'}
    group = Group(idGroup, idLottery, idChat)
    session.add(group)
    session.commit()
    return {'message': 'posted group successfully'}





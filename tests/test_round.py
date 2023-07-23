import logging

import pytest
from requests import request
from json import dumps, loads
from uuid import uuid4
import requests
from os import environ
import redis
from time import sleep


REDIS_HOST = environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = environ.get("REDIS_PORT", default=6379)
BTC_HOST = environ.get("BTC_HOST", default="localhost")
BTC_PORT = environ.get("BTC_PORT", default=5001)
DB_HOST = environ.get("DB_HOST", default="localhost")
DB_PORT = environ.get("DB_PORT", default=5000)
DATABASE_URL = f"http://{DB_HOST}:{DB_PORT}/api"


# URLs
user_endpoint = f"{DATABASE_URL}/users"


def test_reset_btc():
    logging.info(BTC_HOST)
    response = request("GET", f"http://{BTC_HOST}:{BTC_PORT}/reset").json()
    assert response['message'] == 'completed'


def test_create_user():

    user_data = {
        "id": 1,
        "alias": "test",
        "firstName": "test",
        "lastName": "test",
    }
    response = requests.request("POST", user_endpoint, json=user_data).json()
    assert "message" in response


def test_no_name():
    user_id_only = {
        "id": 2
    }
    response = requests.request("POST", user_endpoint, json=user_id_only).json()
    assert "message" in response


def test_submit_vote():
    url = f"{DATABASE_URL}/lottery"
    response = requests.request("POST", url).json()
    assert "height" in response
    start_height = response["height"]
    assert 797947 == start_height
    """Check that it's actually working on redis database."""
    commands = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    assert commands.ping()
    cp = commands.pubsub()
    cp.subscribe('test')

    notifications = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    assert notifications.ping()
    np = notifications.pubsub()
    np.subscribe('tg/notify')

    commands.publish('test', start_height)
    m = cp.get_message()
    assert 1 == m["data"]
    m = cp.get_message()
    assert str(start_height).encode() == m["data"]
    commands.publish("tg/bets", dumps(
            {
                "uuid": uuid4().hex, # common thing in software development
                "idUser": 1,
                "idLottery": start_height,
                "userBet": "odd",
                "betSize": 1000,
            }
        ),
    )
    m = np.get_message(timeout=5.0)
    assert 1 == m["data"]
    m = np.get_message(timeout=5.0)
    assert b'{"1": "Submitted bet successfully"}' == m["data"]


def test_normal_round():
    url = f"{DATABASE_URL}/lottery/reset?id={797947}"
    response = requests.request("POST", url).json()
    assert "message" in response
    response = request("GET", f"http://{BTC_HOST}:{BTC_PORT}/reset").json()
    assert response['message'] == 'completed'
    result_height = 0
    for i in range(0, 2):
        response = request("GET", f"http://{BTC_HOST}:{BTC_PORT}/next").json()
        assert response['message'] == 'completed'
        result_height = request("GET", f"http://{BTC_HOST}:{BTC_PORT}/tip").json()
        assert result_height == 797948 + i
    assert result_height == 797949

    notifications = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    assert notifications.ping()
    np = notifications.pubsub()
    np.subscribe('tg/notify')

    m = np.get_message(timeout=5.0)
    assert 1 == m["data"]


def test_double_round():
    # two lotteries, one frozen, one not
    pass


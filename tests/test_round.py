import pytest

from json import dumps, loads
from uuid import uuid4
import requests
from os import environ
import redis
from time import sleep


DB_HOST = environ.get("DB_HOST", default="localhost")
DB_PORT = environ.get("DB_PORT", default=5000)
DATABASE_URL = f"http://{DB_HOST}:{DB_PORT}/api"

def test_create_user():
    url = f"{DATABASE_URL}/users"
    user_data = {
        "id": 1,
        "alias": "test",
        "firstName": "test",
        "lastName": "test",
    }
    response = requests.request("POST", url, json=user_data).json()
    assert "message" in response

def test_lottery_round():
    url = f"{DATABASE_URL}/lottery"
    response = requests.request("POST", url).json()
    assert "height" in response
    start_height = response["height"]
    """Check that it's actually working on redis database."""
    commands = redis.Redis(host='0.0.0.0', port=6379, db=0)
    notifications = redis.Redis(host='0.0.0.0', port=6379, db=0)
    assert commands.ping()
    cp = commands.pubsub()
    cp.subscribe('test')

    notifications = redis.Redis(host='0.0.0.0', port=6379, db=0)
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
    sleep(0.1)
    m = np.get_message()
    assert 1 == m["data"]
    m = np.get_message()
    assert b'{"1": "Submitted bet successfully"}' == m["data"]
    with open("data/blocks.json", "r") as f:
        blocks = loads(f.read())
    n1 = blocks[0]
    n2 = blocks[1]






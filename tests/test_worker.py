# required packages celery[pytest] pytest-celery pytest-redis
import pytest
from pytest_redis import factories
import requests
from pytest_httpserver import HTTPServer

redis_my_proc = factories.redis_proc(port=6379)
redis_my = factories.redisdb('redis_proc')


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("127.0.0.1", 5001)


@pytest.mark.celery(result_backend='redis://')
def test_my_redis(redis_my, httpserver: HTTPServer):
    httpserver.expect_request("/tip").respond_with_json(797948)
    assert requests.get(httpserver.url_for("/tip")).json() == 797948

    """Check that it's actually working on redis database."""
    redis_my.set('test1', 'test')
    redis_my.set('test2', 'test')
    print(redis_my.get("test2"))
    from database.worker import notify_results
    notify_results()





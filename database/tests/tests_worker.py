import pytest
from worker import notify_results


@pytest.mark.celery(result_backend='redis://')
class test_something:

    def test_notify(self):
        notify_results()
        pass

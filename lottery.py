import logging
from datetime import datetime


class Lottery(object):
    """
    This is Lottery object. Pick your fruit
    """
    _start: int
    _state: dict
    _votes: dict

    def __init__(self):
        logging.debug("Lottery object created")
        self._start = datetime.now().timestamp()
        self._state = {
            'strawberry': 0,
            'apple': 0,
            'pear': 0,
            'banana': 0,
        }
        self._votes = {}

    def get_start(self) -> int:
        """
        Returns the moment in time when Lottery has started
        """
        return self._start

    def store_vote(self, action, user):
        if action in self._state.keys():
            self._state[action] += 1
            vote = self._votes
            if user not in self._votes:
                vote[user] = {}
                vote[user][action] = 1
            else:
                vote[user][action] = 1
        else:
            logging.error(f"access to non-existent key {action}")

    def get_scores(self):
        return self._state

    def get_score(self, action):
        return self._state[action]

    def get_user_vote(self, user_id):
        if user_id not in self._votes.keys():
            self._votes[user_id] = {}
        return self._votes[user_id]

    def finish(self):
        pass

if __name__ == "__main__":
    l = Lottery()
    print(l.get_start())
    l.store_vote('strawberry', 'jee')
    l.store_vote('banana', 'jee')
    l.store_vote('pear', 'jee')
    print(l._votes['jee'])
    jeevote = l._votes['jee']
    count = len(jeevote)
    print(count)

    l.store_vote('apple', 'jee')
    #l.increment('foo', 'foo')
    print(l.get_scores())


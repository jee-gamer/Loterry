import logging
from datetime import datetime
from random import randrange, seed


class Lottery(object):
    """
    This is Lottery object. Pick your fruit
    """

    _start: int
    _hits: dict
    _votes: dict

    def __init__(self):
        logging.debug("Lottery object created")
        self._start = datetime.now().timestamp()
        self._hits = {
            "strawberry": 0,
            "apple": 0,
            "pear": 0,
            "banana": 0,
        }
        self._win_hit_map = {
            0: "strawberry",
            1: "apple",
            2: "pear",
            3: "banana",
        }
        self._max_votes = 1
        self._votes = {}
        self._win_hit = -1

    def store_vote(self, action, user):
        if action in self._hits.keys():
            self._hits[action] += 1
            vote = self._votes
            if user in self._votes:
                s = sum([v for v in vote[user].values()])
                if self._max_votes < s:
                    vote[user][action] += 1
            else:
                vote[user] = {action: 1}
        else:
            logging.error(f"access to non-existent key {action}")

    def get_scores(self):
        return self._hits

    def get_score(self, action):
        return self._hits[action]

    def get_user_vote(self, user_id):
        if user_id not in self._votes.keys():
            self._votes[user_id] = {}
        return self._votes[user_id]

    def reset(self):
        self._votes = {}
        self._win_hit = -1

    def finish(self, as_int = False):
        self._win_hit = randrange(0, 3, 1)
        if as_int:
            return self._win_hit
        else:
            return self._win_hit_map[self._win_hit]

    def check_winner(self, user_id):
        if self._win_hit < 0:
            logging.warning(f"requested result from not finished lottery")
            return user_id, 0
        fruit_hit = self._win_hit_map[self._win_hit]
        user_vote = self.get_user_vote(user_id)
        fruits = [f for f in user_vote.keys()]
        if fruit_hit not in fruits:
            return user_id, 0
        counts = [c for c in user_vote.values()]
        return user_id, counts[fruits.index(fruit_hit)]


if __name__ == "__main__":
    lottery = Lottery()
    logging.info("initializing lottery")
    lottery.store_vote("strawberry", "jee")
    lottery.store_vote("banana", "jee")
    lottery.store_vote("pear", "jee")
    result = lottery.get_user_vote("jee")
    assert result == {'strawberry': 1}
    result = lottery.get_scores()
    assert result == {'strawberry': 1, 'apple': 0, 'pear': 1, 'banana': 1}
    logging.info("testing vote-win scenario")
    seed(1)
    winning = lottery.finish()
    assert winning == 'strawberry'
    assert lottery.check_winner("jee") == ('jee', 1)




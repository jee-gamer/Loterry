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
            "strawberry": 0,
            "apple": 0,
            "pear": 0,
            "banana": 0,
        }
        self._votes = {}

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

    def get_top_fruit(self):
        total_count = {}
        top_fruit = "none"
        for user in self._votes.keys():
            votes = self._votes[user]
            for f, v in votes.items():
                if f in total_count.keys():
                    total_count[f] += v
                else:
                    total_count[f] = 0
                v = [v for f, v in total_count.items()]
                fruits = [f for f, v in total_count.items()]
                top_fruit = fruits[v.index(max(v))]
        return top_fruit

    def reset_score(self):
        self._votes = {}

    def finish(self):
        pass

    def calculate_winner(self, fruit1, user_id):
        user_vote = self.get_user_vote(user_id)
        winner = user_id
        fruits = [f for f, c in user_vote.items()]
        counts = [c for f, c in user_vote.items()]
        user_top_fruit = fruits[counts.index(max(counts))]
        global_top_fruit = self.get_top_fruit()
        print(f"user top fruit {user_top_fruit} vs {global_top_fruit}")
        win = 0

        if user_top_fruit == global_top_fruit:
            print(f"user {user_id} won!")
            win = 1
        return winner, win


if __name__ == "__main__":
    lottery = Lottery()
    print(lottery.get_start())
    lottery.store_vote("strawberry", "jee")
    lottery.store_vote("banana", "jee")
    lottery.store_vote("pear", "jee")
    print(lottery._votes["jee"])
    jeevote = lottery._votes["jee"]
    count = len(jeevote)
    print(count)

    lottery.store_vote("apple", "jee")
    # l.increment('foo', 'foo')
    print(lottery.get_scores())

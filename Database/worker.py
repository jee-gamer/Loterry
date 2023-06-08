from celery import Celery
from celery.schedules import crontab
from database import session, Base, User, Bet, Lottery

app = Celery(broker="redis://localhost")

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, bets, name='checking for new vote messages in the queue')
    sender.add_periodic_task(180.0, blocks, name='checking for new blocks in the queue')

    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        ads.s('Happy Mondays!'),
    )

@app.task
def bets():
    print("checking & processing bets")
    users = session.query(User).all()
    for user in users:
        print(user.as_dict())

    lotteries = session.query(Lottery).filter(Lottery.running == 1)
    for lottery in lotteries:
        print(lottery.as_dict())


@app.task
def blocks():
    print("checking & processing blocks")

@app.task
def ads(arg):
    print(f"Ad message {arg}")

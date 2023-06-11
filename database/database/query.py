import datetime
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import User

engine = create_engine("sqlite:///user.db", echo=False)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

# edit table
"""
user = session.query(User).filter_by(idUser=12).first()

if user:
    user.username = "@NewUsername"
    user.firstName = "FirstName"
    user.lastName = "NewLastName"
else:
    logging.warning("user not found")
session.commit()
"""

q = session.query(User).filter(User.firstName == "Jiramate")
print(q.count())
print(f"q.all() = {type(q.all())}")
#print(f"q.one() = {type(q.one())}")


# Create objects
aliases = []
print(f"\tFirst Name\tLast Name\tEnabled")
for u in session.query(User).filter(User.firstName == "Jiramate"):
    print(f"{u.idUser}")
    print(f"\t{u.firstName}\t{u.lastName.strip()}\t\t{u.enabled}")
    #l = u.lottery
    #print(l.idLottery)
    #print(f"\t{l.F1}\t{l.F2}\t\t{l.F3}\t{l.F4}")

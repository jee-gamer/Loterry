import datetime
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import User

engine = create_engine('sqlite:///user.db', echo=False)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

# edit table
user = session.query(User).filter_by(idUser=11).first()

if user:
    user.username = "@NewUsername"
    user.firstName = "FirstName"
    user.lastName = "NewLastName"
else:
    logging.warning("user not found")
session.commit()

# Create objects
aliases = []
print(f"\tFirst Name\tLast Name\tEnabled")

for u in session.query(User).filter(User.firstName == "Jiramate"):
    print(f"\t{u.firstName}\t{u.lastName.strip()}\t\t{u.enabled}")





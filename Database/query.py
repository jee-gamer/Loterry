import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import User

engine = create_engine('sqlite:///user.db', echo=False)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

# Create objects
aliases = []
print(f"\tFirst Name\tLast Name\tEnabled")

for u in session.query(User).filter(User.firstName == "Jiramate"):
    print(f"\t{u.firstName}\t{u.lastName}\t{u.enabled}")




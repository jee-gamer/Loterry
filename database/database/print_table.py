import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import User

engine = create_engine("sqlite:///user.db", echo=False)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

# Create objects
aliases = []
print(f"\tFirst Name\tLast Name\tEnabled")
for u in session.query(User).order_by(User.idUser):
    print(f"\t{u.firstName}\t{u.lastName}\t{u.enabled}")
    aliases.append(u.alias)

if "@notgeld" not in aliases:
    # Create objects
    user = User(7, "@notgeld", "Ilya", "Evdokimov")
    session.add(user)
    # commit the record the database
    session.commit()

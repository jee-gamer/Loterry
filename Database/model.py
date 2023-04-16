from datetime import datetime

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column

import logging

engine = create_engine("sqlite:///user.db", echo=True)

class Base(DeclarativeBase):
    pass

########################################################################
class User(Base):
    """"""

    __tablename__ = "User"

    idUser = mapped_column(Integer, primary_key=True)
    alias = mapped_column(String)
    firstName = mapped_column(String)
    lastName = mapped_column(String)
    createdAt = mapped_column(DateTime)  # timestamp
    updatedAt = mapped_column(DateTime)  # timestamp
    lotteryId = mapped_column(Integer, ForeignKey("Lottery.idLottery"))
    enabled = mapped_column(Boolean)

    lottery = relationship("Lottery", foreign_keys="User.lotteryId")

    # ----------------------------------------------------------------------
    def __init__(self, idUser, alias, firstName, lastName, lottery = None):
        """"""
        self.idUser = idUser
        self.alias = alias
        self.firstName = firstName
        self.lastName = lastName
        self.createdAt = datetime.now()
        self.updatedAt = self.createdAt
        self.lotteryId = lottery
        self.enabled = False


class Lottery(Base):
    """"""

    __tablename__ = "Lottery"

    idLottery = mapped_column(Integer, primary_key=True)
    createdAt = mapped_column(DateTime)
    updatedAt = mapped_column(DateTime)
    F1 = mapped_column(Integer)  # Fruit 1
    F2 = mapped_column(Integer)
    F3 = mapped_column(Integer)
    F4 = mapped_column(Integer)
    enabled = mapped_column(Boolean)

    # ----------------------------------------------------------------------
    def __init__(self, id):
        """"""
        self.idLottery = id
        self.F1 = 0
        self.F2 = 0
        self.F3 = 0
        self.F4 = 0
        self.createdAt = datetime.now()
        self.updatedAt = self.createdAt
        self.enabled = False


# create tables
Base.metadata.create_all(engine)

if __name__ == "__main__":

    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    # create a Session
    Session = sessionmaker(bind=engine)
    session = Session()

    lottery = Lottery(id=0)
    session.add(lottery)
    session.commit()

    # Create objects
    user = User(11, "@NotJaykayy", "Jiramate", "Kedmake", lottery.idLottery)
    session.add(user)
    user = User(12, "@Someone", "Some", "Some", lottery.idLottery)
    session.add(user)

    # commit the record the database
    session.commit()



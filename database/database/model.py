import random
from datetime import datetime
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
import logging
from random import randrange, choice


class Base(DeclarativeBase):
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    pass


class User(Base):
    __tablename__ = "User"

    idUser = mapped_column(Integer, primary_key=True)
    alias = mapped_column(String)
    firstName = mapped_column(String)
    lastName = mapped_column(String)
    createdAt = mapped_column(DateTime)  # timestamp
    updatedAt = mapped_column(DateTime)
    balance = mapped_column(Integer)
    enabled = mapped_column(Boolean)

    def __init__(self, idUser, alias, firstName, lastName):
        """"""
        self.idUser = idUser
        self.alias = alias
        self.firstName = firstName
        self.lastName = lastName
        self.createdAt = datetime.now()
        self.updatedAt = self.createdAt
        self.enabled = False
        self.balance = 0


class Lottery(Base):
    __tablename__ = "Lottery"

    idLottery = mapped_column(Integer, primary_key=True)
    createdAt = mapped_column(DateTime)
    winningHash = mapped_column(Integer)

    def __init__(self, startedHeight):
        """"""
        self.idLottery = startedHeight
        self.winningHash = None
        self.createdAt = datetime.now()


class Bet(Base):
    __tablename__ = "Bet"
    idBet = mapped_column(String(length=36), primary_key=True)
    idUser = mapped_column(Integer, ForeignKey("User.idUser"))
    idLottery = mapped_column(Integer, ForeignKey("Lottery.idLottery"))
    userBet = mapped_column(Integer)
    betSize = mapped_column(Integer)
    createdAt = mapped_column(DateTime)

    lottery = relationship("Lottery", foreign_keys="Bet.idLottery")
    user = relationship("User", foreign_keys="Bet.idUser")

    def __init__(self, idBet, idUser, idLottery, userBet, betSize):
        self.idBet = idBet
        self.idUser = idUser
        self.idLottery = idLottery
        self.userBet = userBet
        self.betSize = betSize
        self.createdAt = datetime.now()


if __name__ == "__main__":
    pass
    # engine = create_engine("sqlite:///user.db", echo=True)
    # # create tables
    # Base.metadata.create_all(engine)
    #
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    # # create a Session
    # Session = sessionmaker(bind=engine)
    # session = Session()
    #
    # lottery = Lottery(idLottery=0)
    # session.add(lottery)
    # session.commit()
    #
    # # Create objects
    # user = User(11, "@NotJaykayy", "Jiramate", "Kedmake")
    # session.add(user)
    # user = User(12, "@Someone", "Some", "Some")
    # session.add(user)
    # userVote = Bet(11, 1, 1)
    # session.add(userVote)
    # userVote = Bet(9, 1, 1)
    # session.add(userVote)
    # # commit the record the database
    # session.commit()

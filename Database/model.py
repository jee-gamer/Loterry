from datetime import datetime

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

engine = create_engine("sqlite:///user.db", echo=True)
Base = declarative_base()


########################################################################
class User(Base):
    """"""

    __tablename__ = "User"

    idUser = Column(Integer, primary_key=True)
    alias = Column(String)
    firstName = Column(String)
    lastName = Column(String)
    createdAt = Column(String)  # timestamp
    updatedAt = Column(String)  # timestamp
    enabled = Column(Boolean)

    # ----------------------------------------------------------------------
    def __init__(self, idUser, alias, firstName, lastName):
        """"""
        self.idUser = idUser
        self.alias = alias
        self.firstName = firstName
        self.lastName = lastName
        self.createdAt = datetime.now().timestamp()
        self.updatedAt = self.createdAt
        self.enabled = False


# create tables
Base.metadata.create_all(engine)

from datetime import datetime

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
import logging

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
    createdAt = Column(Integer)  # timestamp
    updatedAt = Column(Integer)  # timestamp
    F1 = Column(Integer) # Fruit 1
    F2 = Column(Integer)
    F3 = Column(Integer)
    F4 = Column(Integer)
    enabled = Column(Boolean)

    # ----------------------------------------------------------------------
    def __init__(self, idUser, alias, firstName, lastName):
        """"""
        self.idUser = idUser
        self.alias = alias
        self.firstName = firstName
        self.lastName = lastName
        self.F1 = 0
        self.F2 = 0
        self.F3 = 0
        self.F4 = 0
        self.createdAt = datetime.now().timestamp()
        self.updatedAt = self.createdAt
        self.enabled = False


# create tables
Base.metadata.create_all(engine)

if __name__ == "__main__":

    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    # create a Session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create objects
    user = User(11121, "@NotJaykayy", "Jiramate", "Kedmake")
    session.add(user)

    # commit the record the database
    session.commit()

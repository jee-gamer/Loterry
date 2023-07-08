from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .model import Base

DB_LOCATION = environ.get("DB_LOCATION", default="sqlite:////db/user.db")

engine = create_engine(DB_LOCATION, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .model import Base

engine = create_engine("sqlite:////db/user.db", echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
from .model import *

engine = create_engine("sqlite:///user.db", echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


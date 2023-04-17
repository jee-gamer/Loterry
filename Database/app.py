from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.serving import run_simple

# DB Stuff
from Database.database import Base, User, Bet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
#db = SQLAlchemy(app)

engine = create_engine('sqlite:////tmp/test.db', echo=False)
Base.metadata.create_all(engine)


@app.route("/users")
def get_users():
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(11, "@NotJaykayy", "Jiramate", "Kedmake")
    session.add(user)
    user = User(12, "@Someone", "Some", "Some")
    session.add(user)
    session.commit()
    output = ""
    for u in session.query(User):
        output += f"\t{u.firstName}\t{u.lastName.strip()}\t\t{u.enabled}\n"
    return f"<p>{output}</p>"


@app.route("/users")
def get_users_vote():
    Session = sessionmaker(bind=engine)
    session = Session()
    user = Bet(11, 999, 1)
    session.add(user)
    user = Bet(12, 999, 4)
    session.add(user)
    session.commit()
    output = ""
    for b in session.query(Bet):
        output += f"\t{b.idUser}\t{b.idLottery}\t\t{b.userBet}\n"
    return f"<p>{output}</p>"


if __name__ == '__main__':
    run_simple('localhost', 5000, app,
               use_reloader=True, use_debugger=True, use_evalex=True)

# URI
# http://localhost:5000
# http -- protocol, also possible HTTPS
# local-host -- my PC or server of 192.1.1.2 -- IP address
# 5000 -- the port
# GET / HTTP/1.1" 200
# GET type of HTTP request, for example POST, PUT, DELETE etc
# HTTP/1.1 -- protocol, may be HTTPS
# 200 - Code of the response


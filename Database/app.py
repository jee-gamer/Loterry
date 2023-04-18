from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.serving import run_simple

import Database.app
# DB Stuff
from Database.database import Base, User, Bet, Lottery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'  # root is in big Database file
db = SQLAlchemy(app)

engine = create_engine('sqlite:///user.db', echo=True)
Base.metadata.create_all(engine)


@app.route("/users")
def get_users():

    output = ""
    for u in session.query(User):
        output += f"\t{u.firstName}\t{u.lastName.strip()}\t\t{u.enabled}<br>"
    return f"<p>{output}</p>"


@app.route("/users_vote")
def get_users_vote():

    output = ""
    for b in session.query(Bet):
        output += f"\t{b.idBet}\t{b.idUser}\t{b.idLottery}\t\t{b.userBet}<br>"
    return f"<p>{output}</p>"


@app.route("/lottery")
def lottery_list():

    output = ""
    for lottery in session.query(Lottery):
        output += f"\t{lottery.idLottery}\t{lottery.createdAt}\t{lottery.running}<br>"
    return f"<p>{output}</p>"


@app.route("/add_user", methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        id = request.form['id']
        user = User(id, "@EEE", "yeah", "deez")
        session.add(user)
        session.commit()
        return 'User added to database'
    else:
        return render_template('add_user.html')


if __name__ == '__main__':
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    # create a Session
    Session = sessionmaker(bind=engine)
    session = Session()

    lottery = Lottery(4245577817787)
    session.add(lottery)
    session.commit()

    # Create objects
    user = User(11, "@NotJaykayy", "Jiramate", "Kedmake")
    session.add(user)
    session.commit()
    user = User(12, "@Someone", "Some", "Some")
    session.add(user)
    userVote = Bet(1, 9, 1, 1)
    session.add(userVote)
    userVote = Bet(2, 11, 1, 1)
    session.add(userVote)
    # commit the record the database
    session.commit()

    run_simple('localhost', 5000, app,
               use_reloader=False, use_debugger=True, use_evalex=True)

# URI
# http://localhost:5000
# http -- protocol, also possible HTTPS
# local-host -- my PC or server of 192.1.1.2 -- IP address
# 5000 -- the port
# GET / HTTP/1.1" 200
# GET type of HTTP request, for example POST, PUT, DELETE etc
# HTTP/1.1 -- protocol, may be HTTPS
# 200 - Code of the response


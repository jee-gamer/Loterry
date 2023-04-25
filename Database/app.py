from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.serving import run_simple
import json
import Database.app

# DB Stuff
from Database.database import Base, User, Bet, Lottery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import logging

app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "sqlite:///user.db"  # root is in big Database file
db = SQLAlchemy(app)

engine = create_engine("sqlite:///user.db", echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


# REST Application Programming Interface
@app.route("/api/users", methods=["GET", "POST"])
def api_users():
    if request.method == "POST":
        # curl -X POST "http://localhost:5000/api/users" -d '{"id": 1,"alias": "some","firstName": "some","lastName": "some"}' -H 'Content-Type: application/json'
        try:
            data = request.get_json()
        except Exception as e:
            logging.error(f"Error parsing request data: {e}")
            return jsonify({"status": "error", "result": "couldn't parse request"})

        if "id" not in data.keys():
            return jsonify({"status": "error", "result": "incorrect payload"})

        q = session.query(User).filter(User.idUser == data["id"])
        if q.count() == 1:
            return jsonify({"status": "ok", "result": q.one().as_dict()})

        id = data["id"]
        alias = data["alias"]
        firstName = data["firstName"]
        lastName = data["lastName"]
        user = User(id, alias, firstName, lastName)
        session.add(user)
        session.commit()
        return jsonify({"status": "ok", "result": user.as_dict()})

    else:
        return jsonify([u.as_dict() for u in session.query(User)])


@app.route("/add_user")
def add_user():
    if request.method == "POST":
        user = session.query(User).filter(User.idUser == request.form["id"]).one()

        if user:
            return render_template("message.html", message="User already exists")

        id = request.form["id"]
        alias = request.form["alias"]
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        user = User(id, alias, firstName, lastName)
        session.add(user)
        session.commit()

        return render_template("message.html", message="User added to database")
    else:
        size = len(session.query(User).all()) + 1
        return render_template("add_user.html", lastId=size)


@app.route("/api/users_vote")
def get_api_users_vote():
    return jsonify([v.as_dict() for v in session.query(Bet)])


@app.route("/api/lottery", methods=["GET", "POST"])
def api_lottery_list():
    if request.method == "POST":
        try:
            data = request.get_json()
        except Exception as e:
            logging.error(f"Error parsing request data: {e}")
            return jsonify({"status": "error", "result": "couldn't parse request"})

        if "idLottery" not in data.keys():
            print('incorrect')
            return jsonify({"status": "error", "result": "incorrect payload"})

        q = session.query(Lottery).filter(Lottery.idLottery == data["idLottery"])
        if q.count() == 1:
            print('incorrect2')
            return jsonify({"status": "ok", "result": q.one().as_dict()})

        idLottery = data["idLottery"]
        lottery = Lottery(idLottery)
        session.add(lottery)
        session.commit()
        return jsonify({"status": "ok", "result": lottery.as_dict()})

    else:
        return jsonify([l.as_dict() for l in session.query(Lottery)])


@app.route("/api/lottery/winning_fruit")
def api_lottery_winning_fruit():
    return jsonify([l.winningFruit for l in session.query(Lottery)])


# User Interface in Browser
@app.route("/users")
def get_users():
    output = ""
    for u in session.query(User):
        output += f"\t{u.firstName}\t{u.lastName.strip()}\t\t{u.enabled}\n"
    return render_template("message.html", message=f"{output}")


@app.route("/users_vote")
def get_users_vote():
    output = ""
    for b in session.query(Bet):
        output += f"\t{b.idBet}\t{b.idUser}\t{b.idLottery}\t\t{b.userBet}\n"
    return render_template("message.html", message=f"{output}")


@app.route("/lottery")
def lottery_list():
    output = ""
    for lottery in session.query(Lottery):
        output += f"\t{lottery.idLottery}\t{lottery.createdAt}\t{lottery.running}\n"
    return render_template("message.html", message=f"{output}")


if __name__ == "__main__":
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    # create a Session

    # lottery = Lottery(4787)
    # session.add(lottery)
    # session.commit()
    #
    # # Create objects
    # user = User(11, "@NotJaykayy", "Jiramate", "Kedmake")
    # session.add(user)
    # session.commit()
    # user = User(12, "@Someone", "Some", "Some")
    # session.add(user)
    # userVote = Bet(1, 9, 1, 1)
    # session.add(userVote)
    # userVote = Bet(2, 11, 1, 1)
    # session.add(userVote)
    # # commit the record the database
    # session.commit()

    run_simple(
        "localhost", 5000, app, use_reloader=False, use_debugger=True, use_evalex=True
    )

# need to get
# lottery start time
# max votes
# time left
# vote from specific user on specific lottery
# winning fruit

# URI
# http://localhost:5000
# http -- protocol, also possible HTTPS
# local-host -- my PC or server of 192.1.1.2 -- IP address
# 5000 -- the port
# GET / HTTP/1.1" 200
# GET type of HTTP request, for example POST, PUT, DELETE etc
# HTTP/1.1 -- protocol, may be HTTPS
# 200 - Code of the response

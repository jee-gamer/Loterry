import asyncio
from client import BlockstreamClient
from flask import Flask, jsonify, request
import json
import logging

app = Flask(__name__)
bitcoin_client = BlockstreamClient()

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


@app.route("/", methods=["GET", "POST"])
def index():
    logging.warning(f"request was {request.method}")
    if request.method == "POST":
        try:
            d = json.loads(request.data)
            logging.warning(f"data {d}")
        except Exception as e:
            logging.error(f"{e}")
            return jsonify({"error": "ill formatted json"}), 200
    return jsonify({"jees": "says hello"}), 200


@app.route("/tip")
def get_current_hash():
    hash = asyncio.run(bitcoin_client.get_current_hash())
    if not hash:
        return jsonify({'message': 'error with request'}), 404
    return jsonify({"tip": hash})


@app.route("/block/<hash>")
def get_block(hash):
    data = asyncio.run(bitcoin_client.get_block(hash))
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return jsonify(data)


@app.route("/block/<hash>")
def get_block_status(hash):
    data = bitcoin_client.get_block_status(hash)
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return data

@app.route("/lastblocks")
def get_all_block():
    data = bitcoin_client.get_all_block()
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return data


if __name__ == "__main__":
    app.run(debug=True)

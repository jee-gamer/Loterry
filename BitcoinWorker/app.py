import connexion
from client import BlockstreamClient
from flask import jsonify
import logging

application = connexion.FlaskApp(__name__)

bitcoin_client = BlockstreamClient()

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


def get_current_hash():
    data = bitcoin_client.get_current_hash()
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return jsonify(data)


def get_block(hash):
    data = bitcoin_client.get_block(hash)
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return jsonify(data)


def get_block_status(hash):
    data = bitcoin_client.get_block_status(hash)
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return data


def get_all_block():
    data = bitcoin_client.get_all_block()
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return data


if __name__ == "__main__":
    application.run(debug=True)

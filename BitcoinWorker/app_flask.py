import asyncio
from client import BlockstreamClient
from flask import Flask, jsonify, request
import json
import logging
from multiprocessing import Process, set_start_method


app = Flask(__name__)
bitcoin_client = BlockstreamClient()

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


@app.route("/", methods=["GET", "POST"])  # home page
async def index():
    tip, hash = await bitcoin_client.get_tip()
    return jsonify({"status": "ok", "tip": tip, "hash": hash}), 200


@app.route("/tip")
async def get_current_hash():
    hash = await bitcoin_client.get_current_hash()
    if not hash:
        return jsonify({'message': 'error with request'}), 404
    return jsonify({"tip": hash})

"""
@app.route("/block/<hash>")
def get_block(hash):
    print(hash)
    data = asyncio.run(bitcoin_client.get_block(hash))
    if not data:
        print(f"Error: no data. Blockstream returned {data}")
        return jsonify({'message': 'error with request'}), 404
    return jsonify(data)


@app.route("/block/status")
def get_block_status(hash):
    data = asyncio.run(bitcoin_client.get_block_status(hash))
    if not data:
        return jsonify({'message': 'error with request'}), 404
    return data

@app.route("/lastblocks")
def get_all_block():
    data = asyncio.run(bitcoin_client.get_all_block())
    if not data:
        return jsonify({'message': 'error with request'}), 404

    return data
"""

if __name__ == "__main__":
    """
    set_start_method('spawn')
    heavy_process = Process(  # Create a daemonic process with heavy "my_func"
        target=asyncio.run(bitcoin_client.sync_tip()),
        daemon=True
    )
    heavy_process.start()
    """
    app.run(debug=True)
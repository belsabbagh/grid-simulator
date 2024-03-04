from typing import Callable
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import socket

app = Flask(__name__)


def make_state_buffer():
    buffer = []

    def append_state(state):
        buffer.append(state)

    def fetch_next_state():
        if not buffer:
            return None
        state = buffer.pop(0)
        state["remaining"] = len(buffer)
        return state
    
    def immutable_iterator():
        for state in buffer:
            yield state.copy()

    def clear_state():
        buffer.clear()

    return append_state, fetch_next_state, immutable_iterator, clear_state


def create_flask_state_server(
    web_ui_address,
    fetch_next_state,
    cors_endpoints=None,
) -> Callable[[], None]:
    if cors_endpoints is None:
        cors_endpoints = ["/next"]

    cors_resources = {
        endpoint: {"origins": web_ui_address} for endpoint in cors_endpoints
    }
    cors = CORS(app, resources=cors_resources)

    @app.route("/next", methods=["GET"])
    def _():
        state = fetch_next_state()
        return jsonify(state)

    def start_server():
        app.run()

    return start_server

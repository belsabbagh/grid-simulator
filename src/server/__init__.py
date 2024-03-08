from typing import Callable
from flask import Flask, jsonify
from flask_cors import CORS


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


def create_flask_server(
    record,
    fetch_next_state,
    cors_endpoints=None,
) -> Callable[[], None]:
    app = Flask(__name__)
    if cors_endpoints is None:
        cors_endpoints = [
            r"/*/*",
        ]

    cors_resources = {endpoint: {"origins": "*"} for endpoint in cors_endpoints}
    cors = CORS(app, resources=cors_resources)

    @app.route("/realtime/next", methods=["GET"])
    def realtime_next_state():
        state = fetch_next_state()
        return jsonify(state)

    @app.route("/playback/parameters", methods=["GET"])
    def playback_parameters():
        return jsonify({"parameters": record["parameters"]})

    @app.route("/playback/states/<int:idx>", methods=["GET"])
    def playback_states(idx):
        return jsonify({"state": record["states"][idx]})

    def start_server():
        app.run()

    return start_server

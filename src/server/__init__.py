import os
import pickle
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
    runs_folder,
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
    
    record = None

    @app.route("/realtime/next", methods=["GET"])
    def realtime_next_state():
        state = fetch_next_state()
        return jsonify(state)
    
    @app.route("/runs", methods=["GET"])
    def playback_runs():
        return jsonify({"runs": [os.path.splitext(f)[0] for f in os.listdir(runs_folder)]})

    @app.route("/runs/<string:run_id>", methods=["GET"])
    def playback_parameters(run_id):
        nonlocal record
        with open(os.path.join(runs_folder, run_id + ".pkl"), "rb") as f:
            record = pickle.load(f)
        return jsonify({"parameters": record["parameters"]})

    @app.route("/runs/<string:run_id>/states/<int:idx>", methods=["GET"])
    def playback_states(run_id,idx):
        nonlocal record
        if record is None:
            return jsonify({"error": "No record loaded"})
        return jsonify(record["states"][idx])

    def start_server():
        app.run()

    return start_server

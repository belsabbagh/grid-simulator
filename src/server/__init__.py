import os
import pickle
from flask import Flask, jsonify
from flask_cors import CORS
import datetime
import threading
from timeit import default_timer

from src.core.util.buffer import make_buffer
from src.simulators import synchronous
from src.config import (
    SERVER_ADDRESS,
    NUM_METERS,
    START_DATE,
    END_DATE,
    INCREMENT_MINUTES,
    REFRESH_RATE,
)


def create_flask_server(
    runs_folder,
    cors_endpoints=None,
):
    append_state, fetch_next_state, _, _ = make_buffer()

    def make_simulate_thread():
        init_start = default_timer()
        simulate = synchronous.make_simulate(NUM_METERS, SERVER_ADDRESS, append_state)

        simulate_thread = threading.Thread(
            target=simulate,
            args=(
                START_DATE,
                END_DATE,
                datetime.timedelta(minutes=INCREMENT_MINUTES),
                REFRESH_RATE,
            ),
        )
        init_time = default_timer() - init_start
        print(f"Initialization took {init_time:3} seconds.")
        simulate_thread = threading.Thread(
            target=simulate,
            args=(
                START_DATE,
                END_DATE,
                datetime.timedelta(minutes=INCREMENT_MINUTES),
                REFRESH_RATE,
            ),
        )
        return simulate_thread

    app = Flask(__name__)
    if cors_endpoints is None:
        cors_endpoints = [
            r"/*/*",
        ]

    cors_resources = {endpoint: {"origins": "*"} for endpoint in cors_endpoints}
    cors = CORS(app, resources=cors_resources)

    simulate_thread = make_simulate_thread()
    record = None
    record_id = None

    @app.route("/realtime", methods=["GET"])
    @app.route("/realtime/next", methods=["GET"])
    def realtime_next_state():
        state = fetch_next_state()
        return jsonify(state)

    @app.route("/runs", methods=["GET"])
    def playback_runs():
        return jsonify(
            {"runs": [os.path.splitext(f)[0] for f in os.listdir(runs_folder)]}
        )

    @app.route("/runs/<string:run_id>", methods=["GET"])
    def playback_parameters(run_id):
        nonlocal record
        with open(os.path.join(runs_folder, run_id + ".pkl"), "rb") as f:
            record = pickle.load(f)
        return jsonify({"parameters": record["parameters"]})

    @app.route("/runs/<string:run_id>/states/<int:idx>", methods=["GET"])
    def playback_states(run_id, idx):
        nonlocal record
        if record is None:
            return jsonify({"error": "No record loaded"})
        if record_id == run_id:
            return jsonify(record["states"][idx])
        raise ValueError("Record not loaded")

    def start_server():
        simulate_thread.start()
        threading.Thread(target=app.run).start()

    return start_server

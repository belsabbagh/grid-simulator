import os
import pickle
from typing import Callable, Optional
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


def get_run(runs_folder: str, run_id: str) -> Optional[dict]:
    """Get a run from the specified folder.

    Args:
        run_id (str): The name of the run.
        runs_folder (str): The folder where the runs are stored.
    Returns:
        Optional[dict]: The run if it exists, otherwise None.
    """
    try:
        with open(os.path.join(runs_folder, run_id + ".pkl"), "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


def get_run_meta(runs_folder: str, run_id: str) -> Optional[dict]:
    """Get the time created of a run."""
    try:
        ctime = os.path.getctime(os.path.join(runs_folder, run_id + ".pkl"))
        run = get_run(runs_folder, run_id)
        if run is None:
            return None
        parameters = run["parameters"]
        del run
        return {
            "id": run_id,
            "created": datetime.datetime.fromtimestamp(ctime),
            "parameters": parameters,
        }
    except FileNotFoundError:
        return None


def create_flask_server(
    runs_folder: str,
) -> Callable[[], None]:
    """Create a Flask server that serves the next state of a real-time simulation and the recorded runs in the specified folder.

    Args:
        runs_folder (str): The folder where the recorded runs are stored.
    Returns:
        Callable[[], None]: A function that starts the server.
    """
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
    cors_resources = {r"/*/*": {"origins": "*"}}
    cors = CORS(app, resources=cors_resources)

    simulate_thread = make_simulate_thread()
    record = None

    @app.route("/realtime/next", methods=["GET"])
    def realtime_next_state():
        state = fetch_next_state()
        return jsonify(state)

    @app.route("/runs", methods=["GET"])
    def playback_runs():
        return jsonify(
            {
                "runs": [
                    get_run_meta(runs_folder, os.path.splitext(f)[0])
                    for f in os.listdir(runs_folder)
                ]
            }
        )

    @app.route("/runs/<string:run_id>", methods=["GET"])
    def playback_parameters(run_id):
        nonlocal record
        record = get_run(runs_folder, run_id)
        if record is None:
            raise FileNotFoundError(f"Run {run_id} not found.")
        return jsonify({"parameters": record["parameters"]})

    @app.route("/runs/<string:run_id>/states/<int:idx>", methods=["GET"])
    def playback_states(run_id, idx):
        nonlocal record
        if record is None:
            return jsonify({"error": "No record loaded"})
        return jsonify(record["states"][idx])

    def start_server():
        simulate_thread.start()
        threading.Thread(target=app.run).start()

    return start_server

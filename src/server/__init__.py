from crypt import methods
import os
import pickle
from typing import Callable, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import threading
from timeit import default_timer

from src.core.util.buffer import make_buffer
from src.core.util.dumper import mk_dumper
from src.simulators import synchronous
from src.config import (
    SERVER_ADDRESS,
    INCREMENT_MINUTES,
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
        del parameters["INCREMENT_MINUTES"]
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
    append_state, fetch_next_state, immutable_iter, _ = make_buffer()

    app = Flask(__name__)
    cors_resources = {r"/*/*": {"origins": "*"}}
    cors = CORS(app, resources=cors_resources)
    running = False
    record = None

    simulate = synchronous.make_simulate(SERVER_ADDRESS, append_state)

    @app.route("/realtime/next", methods=["GET"])
    def realtime_next_state():
        state = fetch_next_state()
        return jsonify(state)

    def run(num_meters, start_date, end_date, increment):
        nonlocal running
        running = True
        start = datetime.datetime.now()
        simulate(num_meters, start_date, end_date, increment, 0)
        end = datetime.datetime.now()
        dump = mk_dumper() # The dumper knows how to dump the format you want. you just write the file name as .json or .pkl
        dump(
            {
                "debug": {
                    "time_taken": f"{end - start}",
                },
                "parameters": {
                    "START_DATE": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "END_DATE": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "NUM_METERS": num_meters,
                },
                "states": list(immutable_iter()),
            },
            f"out/runs/server_dump{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.pkl",
        )
        running = False
        
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
        
    @app.route("/runs/running", methods=["GET"])
    def is_running():
        return jsonify({"running": running})

    @app.route("/runs/start", methods=["POST"])
    def start_run():
        init_start = default_timer()
        if request.json is None:
            raise ValueError("Request is None.")
        if running:
            return jsonify({"status": "failed", "message": "A run is already in progress."})
        num_meters = int(request.json["numMeters"])
        start_date = datetime.datetime.fromisoformat(request.json["startDate"])
        end_date = datetime.datetime.fromisoformat(request.json["endDate"])
        simulate_thread = threading.Thread(target=run, args=(num_meters, start_date, end_date, datetime.timedelta(minutes=INCREMENT_MINUTES)))
        init_time = default_timer() - init_start
        simulate_thread.start()
        print(f"Initialization took {init_time:3} seconds.")
        return jsonify({"status": "started", "init_time": init_time})


    @app.route("/runs/<string:run_id>", methods=["GET"])
    def playback_parameters(run_id):
        nonlocal record
        record = get_run(runs_folder, run_id)
        if record is None:
            raise FileNotFoundError(f"Run {run_id} not found.")
        record["parameters"]["INCREMENT_MINUTES"] = INCREMENT_MINUTES
        return jsonify({"parameters": record["parameters"]})

    @app.route("/runs/<string:run_id>/states/<int:idx>", methods=["GET"])
    def playback_states(run_id, idx):
        nonlocal record
        if record is None:
            return jsonify({"error": "No record loaded"})
        return jsonify(record["states"][idx])

    def start_server():
        app.run()

    return start_server

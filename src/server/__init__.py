import os
import pickle
from typing import Callable, Optional
from flask import Flask, Response, json, jsonify, request
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
from src.types import SimulateFunction


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

    app = Flask(__name__)
    cors_resources = {r"/*/*": {"origins": "*"}}
    cors = CORS(app, resources=cors_resources)
    record = None

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

    @app.route("/runs", methods=["POST"])
    def start_run():
        init_start = default_timer()
        if request.json is None:
            raise ValueError("Request is None.")
        try:
            data = request.json
            num_meters = int(data.get("numMeters"))
            start_date_str = data.get("startDate")

            # NOTE: We don't parse "endDate" yet, as it will be calculated/overridden.

            if not all([num_meters, start_date_str]):
                return jsonify(
                    {"error": "Missing numMeters or startDate in request body."}
                ), 400

            start_date = datetime.datetime.fromisoformat(start_date_str)

        except ValueError as e:
            # Catch errors from int() or fromisoformat()
            return jsonify({"error": f"Invalid data format provided: {e}"}), 400
        except Exception:
            # Catch other potential errors like missing JSON
            return jsonify(
                {"error": "Invalid request body format (must be JSON)."}
            ), 400

        now = datetime.datetime.now()

        if start_date >= now:
            return jsonify(
                {
                    "error": f"Start date must be in the past. Provided: {start_date.isoformat()}"
                }
            ), 400
        MAX_METERS = 30
        if num_meters > MAX_METERS:
            return jsonify(
                {
                    "error": f"Number of meters cannot exceed {MAX_METERS}. Provided: {num_meters}"
                }
            ), 400

        time_delta = datetime.timedelta(hours=24)
        end_date = start_date + time_delta
        append_state, fetch_next_state, immutable_iter, _ = make_buffer()
        simulate = synchronous.make_simulate(append_state)
        simulate_thread = threading.Thread(
            target=simulate,
            args=(
                num_meters,
                start_date,
                end_date,
                datetime.timedelta(minutes=INCREMENT_MINUTES),
            ),
        )
        init_time = default_timer() - init_start
        simulate_thread.start()
        print(f"Initialization took {init_time:3} seconds.")

        def stream():
            run_start = default_timer()
            yield (
                json.dumps(
                    {
                        "status": "running",
                        "parameters": {
                            "START_DATE": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "END_DATE": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "NUM_METERS": num_meters,
                        },
                    }
                )
                + "\n"
            )

            # Stream the states
            while simulate_thread.is_alive():
                state = fetch_next_state()
                if state is None:
                    continue
                yield json.dumps({"state": state}) + "\n"
            result = json.dumps(
                {
                    "states": list(immutable_iter()),
                    "status": "done",
                    "debug": {
                        "time_taken": f"{default_timer() - run_start}",
                    },
                    "parameters": {
                        "START_DATE": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "END_DATE": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "NUM_METERS": num_meters,
                    },
                }
            )
            yield result

        return Response(stream(), mimetype="text/event-stream")  # type:ignore

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

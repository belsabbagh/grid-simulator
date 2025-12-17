from typing import Callable
from flask import Flask, Response, json, jsonify, request
from flask_cors import CORS
import datetime
import threading
from timeit import default_timer

from src.core.util.buffer import make_buffer
from src.simulators import synchronous
from src.config import (
    INCREMENT_MINUTES,
)


def create_flask_server() -> Callable[[], None]:
    """Create a Flask server that serves the next state of a real-time simulation and the recorded runs in the specified folder.

    Args:
        runs_folder (str): The folder where the recorded runs are stored.
    Returns:
        Callable[[], None]: A function that starts the server.
    """

    app = Flask(__name__)
    cors_resources = {r"/*/*": {"origins": "*"}}
    _ = CORS(app, resources=cors_resources)

    @app.route("/runs", methods=["POST"])
    def run():
        init_start = default_timer()
        if request.json is None:
            raise ValueError("Request is None.")
        try:
            data = request.json
            num_meters = int(data.get("numMeters"))
            start_date_str = data.get("startDate")

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

    def start_server():
        app.run()

    return start_server

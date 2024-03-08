import datetime
import pickle
import threading
from timeit import default_timer
from src.server import create_flask_server, make_state_buffer
from src.server.sim import make_simulation_server
from src.config import (
    SERVER_ADDRESS,
    NUM_METERS,
    START_DATE,
    END_DATE,
    INCREMENT_MINUTES,
    REFRESH_RATE,
)


if __name__ == "__main__":
    init_start = default_timer()
    record_path = "out/runs"
    append_state, fetch_next_state, _,_ = make_state_buffer()
    simulate = make_simulation_server(NUM_METERS, SERVER_ADDRESS, append_state)
    start_server = create_flask_server(
        record_path,
        fetch_next_state,
    )
    simulate_thread = threading.Thread(target=simulate, args=(
        START_DATE,
        END_DATE,
        datetime.timedelta(minutes=INCREMENT_MINUTES),
        REFRESH_RATE,
    ))
    server_thread = threading.Thread(target=start_server)
    init_time = default_timer() - init_start
    print(f"Initialization took {init_time:3} seconds.")
    # simulate_thread.start()
    server_thread.start()

    # simulate_thread.join()
    server_thread.join()

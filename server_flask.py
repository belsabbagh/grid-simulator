import datetime
import threading
from timeit import default_timer

from src.presets import mk_default_run
from src.server import create_flask_state_server, make_state_buffer
from src.server.sim import make_simulation_server
from src.config import (
    SERVER_ADDRESS,
    NUM_HOUSES,
    START_DATE,
    END_DATE,
    INCREMENT_MINUTES,
    REFRESH_RATE,
    WEB_UI_URL,
)


if __name__ == "__main__":
    init_start = default_timer()
    append_state, fetch_next_state, _,_ = make_state_buffer()
    simulate = make_simulation_server(NUM_HOUSES, SERVER_ADDRESS, append_state)
    default_run = mk_default_run()
    start_server = create_flask_state_server(
        WEB_UI_URL,
        fetch_next_state,
    )
    simulate_thread = threading.Thread(target=simulate, args=(
        START_DATE,
        END_DATE,
        datetime.timedelta(minutes=INCREMENT_MINUTES),
        REFRESH_RATE,
        default_run,
    ))
    server_thread = threading.Thread(target=start_server)
    print(f"Initialization took {(default_timer() - init_start):3} seconds.")
    simulate_thread.start()
    server_thread.start()

    simulate_thread.join()
    server_thread.join()

import datetime
import json
from src.presets import mk_default_run
from src.server import make_state_buffer
from src.server.sim import make_simulation_server_state
from src.config import (
    SERVER_ADDRESS,
    NUM_HOUSES,
    START_DATE,
    END_DATE,
    INCREMENT_MINUTES,
    REFRESH_RATE,
)


if __name__ == "__main__":
    append_state, fetch_next_state, immutable_iter, _ = make_state_buffer()
    simulate = make_simulation_server_state(NUM_HOUSES, SERVER_ADDRESS, append_state)
    default_run = mk_default_run()
    start = datetime.datetime.now()
    simulate(
        START_DATE,
        END_DATE,
        datetime.timedelta(minutes=INCREMENT_MINUTES),
        REFRESH_RATE,
        default_run,
    )
    end = datetime.datetime.now()
    print(f"Simulation took {end - start}")
    with open("server_dump.json", "w") as f:
        json.dump(
            {
                "debug": {
                    "time_taken": f"{end - start}",
                },
                "parameters": {
                    "START_DATE": START_DATE.strftime("%Y-%m-%d %H:%M:%S"),
                    "END_DATE": END_DATE.strftime("%Y-%m-%d %H:%M:%S"),
                    "INCREMENT_MINUTES": INCREMENT_MINUTES,
                },
                "states": list(immutable_iter()),
            },
            f,
            default=str,
            indent=2,
        )

import datetime
import json
import os
import pickle
from timeit import default_timer
from src.presets import mk_default_run
from src.server import make_state_buffer
from src.server.sim import make_simulation_server
from src.config import (
    SERVER_ADDRESS,
    NUM_HOUSES,
    START_DATE,
    END_DATE,
    INCREMENT_MINUTES,
    REFRESH_RATE,
)
from src.util.dumper import mk_dumper

if __name__ == "__main__":
    init_start = default_timer()
    append_state, fetch_next_state, immutable_iter, _ = make_state_buffer()
    simulate = make_simulation_server(NUM_HOUSES, SERVER_ADDRESS, append_state)
    default_run = mk_default_run()
    print(f"Initialization took {(default_timer() - init_start):3} seconds.")
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
    dump = mk_dumper() # The dumper knows how to dump the format you want. you just write the file name as .json or .pkl
    dump(
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
        f"out/server_dump{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.pkl",
    )

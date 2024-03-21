import datetime
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
from src.core.util.dumper import mk_dumper

if __name__ == "__main__":
    init_start = default_timer()
    append_state, fetch_next_state, immutable_iter, _ = make_buffer()
    simulate = synchronous.make_simulate(SERVER_ADDRESS, append_state)
    print(f"Initialization took {(default_timer() - init_start):3} seconds.")
    start = datetime.datetime.now()
    simulate(
        NUM_METERS,
        START_DATE,
        END_DATE,
        datetime.timedelta(minutes=INCREMENT_MINUTES),
        REFRESH_RATE,
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
                "NUM_METERS": NUM_METERS,
            },
            "states": list(immutable_iter()),
        },
        f"out/runs/server_dump{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.pkl",
    )

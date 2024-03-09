import time
from src.config import DEVIATION
from src.core.data_generator import mk_grid_state_generator, mk_instance_generator
from src.types import SimulateFunction
from src.core.util import date_range


def make_simulate(n, _, append_state) -> SimulateFunction:
    ids = range(1, n + 1)

    def simulate(start_date, end_date, datetime_delta, refresh_rate):
        data_generator = mk_instance_generator(
            start_date, end_date, datetime_delta, DEVIATION
        )
        grid_state_generator = mk_grid_state_generator()
        for t in date_range(start_date, end_date, datetime_delta):
            grid_state = grid_state_generator(t)
            append_state(
                {
                    "time": t,
                    "grid_state": grid_state,
                    "meters": [
                        {
                            "id": f"{i}",
                            "generation": gen,
                            "consumption": con,
                        }
                        for i, (gen, con) in zip(ids, [data_generator(t) for _ in ids])
                    ],
                }
            )
            print(f"Moment {t} has passed.")
            time.sleep(refresh_rate)

    return simulate

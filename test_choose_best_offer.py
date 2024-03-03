import datetime
import random
import time
from src.core.data_generator import mk_instance_generator, mk_grid_state_generator
from src.core.optimizer import mk_choose_best_offers_function, GridMetrics, Offer
from config import WEB_UI_URL, START_DATE, END_DATE
from src.server import create_flask_state_buffer, make_state_buffer
from src.core.util import date_range
INCREMENT_MINUTES = 1
REFRESH_RATE = 0.5
NUM_HOUSES = 12
START_DATE = datetime.datetime(2010, 1, 1, 10, 0, 0)
END_DATE = datetime.datetime(2010, 1, 1, 19, 0, 0)
DEVIATION = 0.1

efficiency_model_path = "models/grid-loss.h5"
duration_model_path = "models/duration.h5"

data_generator = mk_instance_generator(DEVIATION)
grid_state_generator = mk_grid_state_generator()
choose_best = mk_choose_best_offers_function(
    efficiency_model_path, duration_model_path, efficiency_model_path
)


def get_surplus(gen, con):
    return gen - con


def split_to_deficit_and_surplus(meters):
    groups = [{}, {}]
    for k, v in meters.items():
        groups[not v >= 0][k] = v
    return groups


def fmt_choice(choice: tuple[Offer, float]):
    return f"{choice[0].source} -> {choice[1]:.4f}"


def make_collect_state(append_state):
    def collect_state():
        for t in date_range(START_DATE, END_DATE, datetime.timedelta(minutes=INCREMENT_MINUTES)):
            meters = {
                str(k + 1): get_surplus(*data_generator(t)) for k in range(NUM_HOUSES)
            }
            grid_state = grid_state_generator(t)
            grid_metrics = GridMetrics(
                load=grid_state[0],
                temperature=grid_state[1],
                voltage=grid_state[2],
                intensity=grid_state[3],
            )
            offers_dict, deficits = split_to_deficit_and_surplus(meters)
            offers = [
                Offer(amount=v, source=k, participation_count=random.randint(1, 3))
                for k, v in offers_dict.items()
            ]
            choices = map(
                lambda x: choose_best(deficits[x], offers, grid_metrics), deficits
            )
            best_choices = {
                k: None if not v else fmt_choice(v[0])
                for k, v in zip(deficits.keys(), choices)
            }
            state_data = {
                "timestamp": t.strftime("%H:%M"),
                "meters": meters,
                "grid_metrics": grid_metrics,
                "best_choices": best_choices,
            }
            append_state(state_data)
            time.sleep(REFRESH_RATE)

    return collect_state


def main():
    append_state, fetch_next_state = make_state_buffer()

    start_server = create_flask_state_buffer(
        WEB_UI_URL,
        make_collect_state(append_state),
        fetch_next_state,
    )
    start_server()


if __name__ == "__main__":
    main()

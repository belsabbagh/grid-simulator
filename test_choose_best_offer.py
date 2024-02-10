import datetime
import random
import threading
import time
from src.core.data_generator import mk_instance_generator, mk_grid_state_generator
from src.core.optimizer import mk_choose_best_offers_function, GridMetrics, Offer
from src.gui import OptimizerApp

INCREMENT_MINUTES = 1
REFRESH_RATE = 5
NUM_HOUSES = 25
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
    return f"{choice[0].source} -> {choice[1]}"


def update_ui(app: OptimizerApp):
    t = START_DATE
    while t < END_DATE:
        t += datetime.timedelta(minutes=INCREMENT_MINUTES)
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
        offers = [Offer(amount=v, source=k, participation_count=random.randint(1, 3)) for k, v in offers_dict.items()]
        choices = map(lambda x: choose_best(deficits[x], offers, grid_metrics), deficits)
        best_choices = {k: fmt_choice(v[0]) for k, v in zip(deficits.keys(), choices)}
        app.window.update_meters(meters)
        app.window.update_choices(best_choices)
        app.window.update_timer_label(t.strftime("%H:%M"))
        time.sleep(REFRESH_RATE)



if __name__ == "__main__":
    app = OptimizerApp()
    thread = threading.Thread(target=update_ui, args=(app,))
    thread.start()
    app.exec()
    thread.join()

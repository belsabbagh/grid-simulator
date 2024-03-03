import datetime
from config import WEB_UI_URL
from src.core.data_generator import generate_normal_random_parameters
from src.core.optimizer import mk_predict_function
import time
from src.server import create_flask_state_buffer, make_state_buffer
from src.core.util import date_range, fmt_grid_state



def make_collect_state(append_state):
    def collect_state():
        start = datetime.datetime(2021, 10, 1, 10, 0, 0)
        efficiency_model_path = "models/grid-loss.h5"
        duration_model_path = "models/duration.h5"
        predict_function = mk_predict_function(
            efficiency_model_path, duration_model_path, efficiency_model_path
        )
        for t in date_range(
            start, start + datetime.timedelta(hours=9), datetime.timedelta(minutes=1)
        ):
            parameters = generate_normal_random_parameters(
                [0.4, 20, 239.696, 3.132, 900],
                [0.1, 1, 1, 0.1, 10],
            )
            efficiency, duration = predict_function(*parameters)
            state_data = {
                "timestamp": t.strftime("%H:%M"),
                "parameters": fmt_grid_state(parameters),
                "predictions": {
                    "Expected Efficiency": efficiency,
                    "Expected Duration (hr)": duration,
                },
            }
            append_state(state_data)
            t += datetime.timedelta(minutes=1)
            time.sleep(1)

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

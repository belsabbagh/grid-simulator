import threading
from random import random
import datetime
from src.gui import PredictApp
from src.core.optimizer import mk_predict_function
import time

def generate_normal_random_parameters(means, deviations) -> list[float]:
    # generate a normmally distributed random number for each mean and deviation
    return [random() * deviation + mean for mean, deviation in zip(means, deviations)]


def update_ui(app: PredictApp) -> None:
    t = datetime.datetime(2021, 10, 1, 10, 0, 0)
    efficiency_model_path = "models/grid-loss.h5"
    duration_model_path = "models/duration.h5"
    predict_function = mk_predict_function(
        efficiency_model_path, duration_model_path, efficiency_model_path
    )
    while True:
        parameters = generate_normal_random_parameters(
            [0.4, 20, 239.696, 3.132, 900],
            [0.1, 1, 1, 0.1, 10],
        )
        app.window.update_parameters(
            {
                "Grid load (GWh)": round(parameters[0], 3),
                "Grid temperature (C)": round(parameters[1], 3),
                "Voltage (V)":  round(parameters[2], 3),
                "Global intensity (A)": round(parameters[3], 3),
                "Transaction amount (Wh)": round(parameters[4], 3),
            }
        )
        efficiency, duration = predict_function(*parameters)
        app.window.update_predictions(
            {
                "Expected Efficiency": round(efficiency, 3),
                "Expected Duration (hr)": round(duration, 3)
            }
        )
        app.window.update_timer_label(t.strftime("%H:%M"))
        t += datetime.timedelta(minutes=1)
        time.sleep(1)


if __name__ == "__main__":
    app = PredictApp()
    thread = threading.Thread(target=update_ui, args=(app,))
    thread.start()
    app.exec()
    thread.join()

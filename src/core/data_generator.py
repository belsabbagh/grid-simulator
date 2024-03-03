import datetime as dt
import random
from typing import Callable
import pandas as pd

TIME_FORMAT = "%H:%M:%S"


def sub_time(t1: pd.Timestamp, t2: pd.Timestamp) -> dt.timedelta:
    a: dt.time = t1.time()
    b: dt.time = t2.time()
    return dt.timedelta(
        hours=a.hour - b.hour,
        minutes=a.minute - b.minute,
        seconds=a.second - b.second,
    )


def generate_random(t: dt.time, df: pd.DataFrame, deviation: float) -> float:
    ts = pd.Timestamp(t.strftime(TIME_FORMAT))

    def min_key(x: pd.Timestamp) -> float:
        return abs(sub_time(x, ts).total_seconds())

    closest_time: int = min(df.index, key=min_key)
    closest_value: float = df.loc[closest_time]["value"]
    random_value: float = random.uniform(-deviation, deviation)
    return closest_value + random_value


def mk_gen_df() -> pd.DataFrame:
    """This is where you load the generated power dataframe. The dataframe should have a column named "value" and an index of type datetime.datetime."""
    gen: pd.DataFrame = pd.read_csv("data/gen.txt", sep=";")
    gen.set_index("Time", inplace=True)
    gen.index = pd.to_datetime(gen.index, format=TIME_FORMAT)
    gen = gen[["Simulated_Solar_Power"]]
    gen = gen.rename(columns={"Simulated_Solar_Power": "value"})
    gen["value"] = gen["value"].apply(lambda x: max(0, x))
    gen["value"] = gen["value"] * 5
    return gen


def mk_con_df() -> pd.DataFrame:
    """This is where you load the consumed power dataframe. The dataframe should have a column named "value" and an index of type datetime.datetime."""
    con: pd.DataFrame = pd.read_csv("data/output.txt")
    con.set_index("Time", inplace=True)
    con.index = pd.to_datetime(con.index, format=TIME_FORMAT)
    con = con[["Global_active_power"]].rename(columns={"Global_active_power": "value"})
    return con


def mk_instance_generator(
    d: float,
) -> Callable[[dt.datetime], tuple[float, float]]:
    gen: pd.DataFrame = mk_gen_df()
    con: pd.DataFrame = mk_con_df()

    def instance_generator(t: dt.datetime) -> tuple[float, float]:
        return generate_random(t.time(), gen, d), generate_random(t.time(), con, d)

    return instance_generator


def generate_normal_random_parameters(means, deviations) -> list[float]:
    # generate a normmally distributed random number for each mean and deviation
    return [
        random.random() * deviation + mean for mean, deviation in zip(means, deviations)
    ]


def mk_grid_state_generator():

    means: list[float] = [0.4, 20, 239.696, 3.132]
    devs: list[float] = [0.1, 1, 1, 0.1]

    def generate_grid_state(t: dt.datetime):
        return generate_normal_random_parameters(means, devs)

    return generate_grid_state

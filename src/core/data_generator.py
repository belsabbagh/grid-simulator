import datetime
import random
import pandas as pd

TIME_FORMAT = "%H:%M:%S"


def generate_random(t: datetime.time, df: pd.DataFrame, deviation):
    def sub_time(t1: pd.Timestamp, t2: pd.Timestamp):
        t1, t2 = t1.time(), t2.time()
        return datetime.timedelta(hours=t1.hour - t2.hour, minutes=t1.minute - t2.minute, seconds=t1.second - t2.second)
    # get the closest time from time index
    t = pd.Timestamp(t.strftime(TIME_FORMAT))
    closest_time = min(df.index, key=lambda x: abs(sub_time(x,t).total_seconds()))
    # get the value from the closest time
    closest_value = df.loc[closest_time]["value"]
    # generate random value
    random_value = random.uniform(-deviation, deviation)
    # return the sum of the two
    return closest_value + random_value


def make_instance_generator(d):
    def instance_generator(t: datetime.datetime):
        return max(0, generate_random(t, gen, d)), generate_random(t, con, d)

    gen = pd.read_csv("data/gen.txt", sep=";")
    gen = gen.set_index("Time")
    gen.index = pd.to_datetime(gen.index, format=TIME_FORMAT)
    gen = gen[["Simulated_Solar_Power"]]
    gen = gen.rename(columns={"Simulated_Solar_Power": "value"})
    gen["value"] = gen["value"] * 5

    con = pd.read_csv("data/output.txt")
    con = con.set_index("Time")
    con.index = pd.to_datetime(con.index, format=TIME_FORMAT)
    con = con[["Global_active_power"]]
    con = con.rename(columns={"Global_active_power": "value"})
    return instance_generator
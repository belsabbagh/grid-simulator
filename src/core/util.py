import datetime as dt

import pandas as pd
GRID_STATE_PARAMS = [
    "Grid load (GWh)",
    "Grid temperature (C)",
    "Voltage (V)",
    "Global intensity (A)",
]

def date_range(start: dt.datetime, end: dt.datetime, delta: dt.timedelta):
    current = start
    while current < end:
        yield current
        current += delta

def fmt_grid_state(grid_state: list[float]):
    return {key: value for key, value in zip(GRID_STATE_PARAMS, grid_state)}



def sub_time(t1: pd.Timestamp, t2: pd.Timestamp) -> dt.timedelta:
    a: dt.time = t1.time()
    b: dt.time = t2.time()
    return dt.timedelta(
        hours=a.hour - b.hour,
        minutes=a.minute - b.minute,
        seconds=a.second - b.second,
    )

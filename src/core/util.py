import datetime
GRID_STATE_PARAMS = [
    "Grid load (GWh)",
    "Grid temperature (C)",
    "Voltage (V)",
    "Global intensity (A)",
]

def date_range(start: datetime.datetime, end: datetime.datetime, delta: datetime.timedelta):
    current = start
    while current < end:
        yield current
        current += delta

def fmt_grid_state(grid_state: list[float]):
    return {key: value for key, value in zip(GRID_STATE_PARAMS, grid_state)}

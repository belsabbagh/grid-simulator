from typing import Callable, TypeVar
import datetime as dt

R = TypeVar("R")

TimeGenerator = Callable[[dt.datetime], R]

SimulateFunction = Callable[
    [int, dt.datetime, dt.datetime, dt.timedelta, float], None
]

SocketAddress = tuple[str, int]

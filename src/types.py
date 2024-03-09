from dataclasses import dataclass
from typing import Callable, TypeVar
import datetime as dt

R = TypeVar("R")

TimeGenerator = Callable[[dt.datetime], R]

SimulateFunction = Callable[
    [dt.datetime, dt.datetime, dt.timedelta, float], None
]


@dataclass
class Trade:
    amount: float
    source: str
    destination: str
    timestamp: str
    duration: float
    efficiency: float
    quality: float


@dataclass
class TradeBlock:
    index: int
    body: Trade
    hash: str
    timestamp: str
    nonce: int

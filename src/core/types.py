from dataclasses import dataclass
from typing import Callable, TypedDict

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

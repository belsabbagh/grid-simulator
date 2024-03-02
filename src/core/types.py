from dataclasses import dataclass
from typing import TypedDict


class UIUpdate(TypedDict):
    type: str
    time: str
    meters: dict[tuple[str, int], float]
    trades: dict[tuple[str, int], tuple[str, int]]

@dataclass
class Offer:
    amount: float
    source: str
    participation_count: int


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


@dataclass
class GridMetrics:
    load: float
    temperature: float
    voltage: float
    intensity: float

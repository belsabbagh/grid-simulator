import datetime
from typing import Generator, Optional
from src.types import SocketAddress


def energy_transfer_amount(duration:int, intensity:float, voltage:float) -> float:
    return duration * intensity * voltage


def make_trade_handler():
    trades: dict[SocketAddress, tuple[SocketAddress, float]] = {}

    def add_trade(buyer: SocketAddress, source: SocketAddress, amount: float):
        if source not in trades:
            trades[source] = (buyer, amount)

    def trades_iter() -> (
        Generator[tuple[SocketAddress, tuple[SocketAddress, float]], None, None]
    ):
        yield from trades.items()

    def execute_trade(
        buyer: SocketAddress, duration: datetime.timedelta, voltage: float, intensity: float
    ):
        """This function draws energy from the source according to the duration it takes to transfer the energy and the efficiency of the transfer."""
        if buyer not in trades:
            return False

        source, amount = trades[buyer]

        new_amount = amount - energy_transfer_amount(efficiency, duration.total_seconds(), intensity, voltage)
        if new_amount < 0:
            del trades[buyer]
        
        trades[buyer] = (source, new_amount)

        return True


    def get_trade(source: SocketAddress) -> Optional[tuple[SocketAddress, float]]:
        return trades.get(source, None)

    return add_trade, trades_iter, get_trade, execute_trade

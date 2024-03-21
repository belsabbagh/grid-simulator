import datetime
from typing import Generator, Optional
from src.types import SocketAddress


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
        buyer: SocketAddress, duration: datetime.timedelta, efficiency: float
    ):
        """This function draws energy from the source according to the duration it takes to transfer the energy and the efficiency of the transfer."""
        if buyer not in trades:
            return False

        trades[buyer] = (
            trades[buyer][0],
            trades[buyer][1] - duration.total_seconds() * efficiency,
        )

        return True

    def execute_all_trades(duration: datetime.timedelta, efficiency: float):
        """This function executes all trades."""
        for source in trades:
            execute_trade(source, duration, efficiency)
        for source in list(trades.keys()):
            if trades[source][1] <= 0:
                del trades[source]

    def get_trade(source: SocketAddress) -> Optional[tuple[SocketAddress, float]]:
        return trades.get(source, None)

    return add_trade, trades_iter, get_trade, execute_trade, execute_all_trades

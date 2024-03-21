import datetime
from typing import Optional
from your_module import SocketAddress, make_trade_handler

def test_add_trade():
    add_trade, _, _, _, _ = make_trade_handler()
    buyer = SocketAddress("localhost", 1234)
    source = SocketAddress("localhost", 5678)
    amount = 100.0
    add_trade(buyer, source, amount)
    assert make_trade_handler()[2](source) == (buyer, amount)

def test_execute_trade():
    _, _, _, execute_trade, _ = make_trade_handler()
    buyer = SocketAddress("localhost", 1234)
    source = SocketAddress("localhost", 5678)
    amount = 100.0
    make_trade_handler()[0](buyer, source, amount)
    duration = datetime.timedelta(seconds=10)
    efficiency = 0.8
    assert execute_trade(buyer, duration, efficiency) is True
    assert make_trade_handler()[2](source) == (buyer, amount - duration.total_seconds() * efficiency)

def test_execute_all_trades():
    _, _, _, _, execute_all_trades = make_trade_handler()
    duration = datetime.timedelta(seconds=10)
    efficiency = 0.8
    execute_all_trades(duration, efficiency)
    assert len(make_trade_handler()[1]()) == 0

def test_get_trade():
    _, _, get_trade, _, _ = make_trade_handler()
    buyer = SocketAddress("localhost", 1234)
    source = SocketAddress("localhost", 5678)
    amount = 100.0
    make_trade_handler()[0](buyer, source, amount)
    assert get_trade(source) == (buyer, amount)
    assert get_trade(SocketAddress("localhost", 9876)) is None
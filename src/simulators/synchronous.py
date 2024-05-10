import pickle
import socket
import threading
import time
import socket
from typing import Any, Callable

from src.config import DEVIATION, NUM_METERS
from src.core import trade_handler
from src.core.optimizer import mk_choose_best_offers_function
from src.types import SimulateFunction, SocketAddress
from src.core.util import comms
from src.core.data_generator import mk_grid_state_generator, mk_instance_generator

from src.core.util import date_range, fmt_grid_state


def calc_sizeof_offers_msg(n):
    example_offer = {
        "source": ("localhost", 94065),
        "price": 0.0,
        "amount": 0.0,
    }
    return n * len(pickle.dumps(example_offer))


offers_msg_size = calc_sizeof_offers_msg(NUM_METERS)


def meter_mkthread(
    s: socket.socket, buf_size: int, trade_chooser
) -> Callable[..., threading.Thread]:
    def run() -> None:
        recv_stream: bytes = s.recv(buf_size)
        if not recv_stream:
            return
        data: dict[str, Any] = pickle.loads(recv_stream)
        data_type = data["type"]
        if data_type != "power":
            raise ValueError("Haven't received power data.")
        gen, con = data["generation"], data["consumption"]
        grid_state = data["grid_state"]
        surplus = gen - con
        s.sendall(
            pickle.dumps(
                comms.make_msg_body(
                    s.getsockname(),
                    "surplus",
                    surplus=surplus,
                    generation=gen,
                    consumption=con,
                )
            )
        )
        recv_stream = s.recv(offers_msg_size)
        if not recv_stream:
            return
        data = pickle.loads(recv_stream)
        if data["type"] != "offers":
            return
        if not data["offers"] or surplus >= 0:
            s.sendall(pickle.dumps({"from": s.getsockname(), "trade": None}))
            return
        result = trade_chooser(surplus, data["offers"], grid_state)
        offer, fitness = result[0]
        s.sendall(
            pickle.dumps(
                {"from": s.getsockname(), "trade": offer["source"], "fitness": fitness}
            )
        )

    def mkthread(args=None):
        if args is None:
            args = ()
        return threading.Thread(target=run, args=args)

    return mkthread


def mk_meters_runner(n, server_address, trade_chooser):

    sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(n)]
    for s in sockets:
        s.connect(server_address)
    meters = [meter_mkthread(s, 512, trade_chooser) for s in sockets]

    def meters_runner():
        while True:
            threads = [m() for m in meters]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

    return meters_runner


def make_simulate(server_address, append_state) -> SimulateFunction:
# %%SIMULATION RUNS HERE
    def simulate(n, start_date, end_date, datetime_delta, refresh_rate, optimization_weights=None):
        trade_chooser = mk_choose_best_offers_function(
            "models/grid-loss.json",
            "models/duration.json",
            "models/grid-loss.json",
            weights=optimization_weights
        )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(server_address)
            s.listen(n)
            print("Server started")
            conns: list[tuple[socket.socket, SocketAddress]] = []
            print("Waiting to connect to meters...")
            meters_runner = mk_meters_runner(n, server_address, trade_chooser)
            meters_thread = threading.Thread(target=meters_runner)
            meters_thread.daemon = True
            meters_thread.start()
            for _ in range(n):
                conn, addr = s.accept()
                conns.append((conn, addr))
        data_generator = mk_instance_generator(
            start_date, end_date, datetime_delta, DEVIATION
        )
        grid_state_generator = mk_grid_state_generator()
        for t in date_range(start_date, end_date, datetime_delta):
            grid_state = grid_state_generator(t)
            surplus: dict[SocketAddress, float] = {}
            messages = {}
            for _, addr in conns:
                gen, con = data_generator(t)
                messages[addr] = pickle.dumps(
                    comms.make_msg_body(
                        addr,
                        "power",
                        datetime=t,
                        grid_state=grid_state,
                        generation=gen,
                        consumption=con,
                    )
                )
            comms.send_and_recv_sync(
                conns, messages, surplus, lambda x: pickle.loads(x)["surplus"]
            )
            offers = [
                {"source": addr, "amount": surplus[addr], "participation_count": 1}
                for addr in surplus
                if surplus[addr] > 0
            ]
            messages = {}
            for _, addr in conns:
                messages[addr] = pickle.dumps(
                    comms.make_msg_body(addr, "offers", offers=offers)
                )
            trades = {}
            comms.send_and_recv_sync(
                conns, messages, trades, lambda x: pickle.loads(x)["trade"]
            )
            transfers = {}
            for trade in trades:
                buyer = trade
                source = trades[trade]
                if source is None:
                    continue
                amount = list(filter(lambda x: x["source"] == source, offers))[0][
                    "amount"
                ]
                transfers[buyer] = min(amount, grid_state[-1] * grid_state[-2] * datetime_delta.total_seconds())
            meter_display_ids = {addr: i for i, addr in enumerate(surplus.keys(), 1)}
            meters = [
                {
                    "id": meter_display_ids[addr],
                    "surplus": surplus[addr],
                    "transferred": transfers.get(addr, 0),
                    "in_trade": (
                        meter_display_ids.get(trades.get(addr, None), "")
                        if addr in trades
                        else None
                    ),
                }
                for addr in surplus
            ]
            print(f"Moment {t} has passed.")
            append_state(
                {
                    "time": t.strftime("%H:%M:%S"),
                    "meters": meters,
                    "grid_state": fmt_grid_state(grid_state),
                }
            )
            time.sleep(refresh_rate)

    return simulate

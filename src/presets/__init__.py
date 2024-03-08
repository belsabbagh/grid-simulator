import pickle
import socket
import threading
from typing import Any, Callable
from src.config import NUM_METERS
from src.core.optimizer import mk_choose_best_offers_function


def calc_sizeof_offers_msg(n):
    example_offer = {
        "source": ('localhost', 94065),
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
                {"from": s.getsockname(), "surplus": surplus, "type": "surplus"}
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


def mk_meters_runner(n, server_address):
    trade_chooser = mk_choose_best_offers_function(
        "models/grid-loss.h5",
        "models/duration.h5",
        "models/grid-loss.h5",
    )
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

import threading
import socket
import pickle
import random
from typing import Callable, Any


def meter_mkthread(
    s: socket.socket, buf_size: int, trade_chooser: Callable
) -> Callable[..., threading.Thread]:
    choose = trade_chooser
    
    def run() -> None:
        recv_stream: bytes = s.recv(buf_size)
        if not recv_stream:
            return
        data: dict[str, Any] = pickle.loads(recv_stream)
        data_type = data["type"]
        if data_type != "power":
            raise ValueError("Haven't received power data.")
        gen, con = data["generation"], data["consumption"]
        surplus = gen - con
        s.sendall(
            pickle.dumps(
                {"from": s.getsockname(), "surplus": surplus, "type": "surplus"}
            )
        )
        recv_stream = s.recv(2048)
        if not recv_stream:
            return
        data = pickle.loads(recv_stream)
        if data["type"] != "offers":
            return
        if not data["offers"]:
            s.sendall(pickle.dumps({"from": s.getsockname(), "trade": None}))
            return
        if surplus > 0:
            s.sendall(pickle.dumps({"from": s.getsockname(), "trade": None}))

        source, amount = random.choice(data["offers"])
        s.sendall(pickle.dumps({"from": s.getsockname(), "trade": source}))

    def mkthread(args=None):
        if args is None:
            args = ()
        return threading.Thread(target=run, args=args)

    return mkthread

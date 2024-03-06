import pickle
import socket
import threading
from typing import Any, Callable
from src.config import DEVIATION
from src.core.data_generator import mk_grid_state_generator, mk_instance_generator
from src.core.optimizer import mk_choose_best_offers_function
from src.core.util import fmt_grid_state


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
        recv_stream = s.recv(8192)
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

def mk_default_run():
    data_generator = mk_instance_generator(DEVIATION)
    grid_state_generator = mk_grid_state_generator()

    def surplus_connection(conn, addr, t, grid_state, results):
        gen, con = data_generator(t)
        conn.sendall(
            pickle.dumps(
                {
                    "type": "power",
                    "generation": gen,
                    "consumption": con,
                    "grid_state": grid_state,
                }
            )
        )
        data = pickle.loads(conn.recv(1024))
        results[addr] = data["surplus"]

    def trade_connection(conn, addr, offers, results):
        conn.sendall(pickle.dumps({"type": "offers", "offers": offers}))
        data = pickle.loads(conn.recv(1024))
        results[addr] = data["trade"]

    def run_phase(conns, target, args):
        threads = []
        for conn, addr in conns:
            t1 = threading.Thread(target=target, args=(conn, addr, *args))
            t1.start()
            threads.append(t1)
        for t1 in threads:
            t1.join()

    def moment(t, conns: list[tuple[socket.socket, tuple[str, int]]]):
        grid_state = grid_state_generator(t)
        results: dict[tuple[str, int], float] = {}
        run_phase(conns, surplus_connection, (t, grid_state, results))
        offers = [
            {"source": addr, "amount": results[addr], "participation_count": 1}
            for addr in results
            if results[addr] > 0
        ]
        trades = {}
        run_phase(conns, trade_connection, (offers, trades))
        meter_display_ids = {addr: i for i, addr in enumerate(results.keys(), 1)}
        meters = [
            {
                "id": meter_display_ids[addr],
                "surplus": results[addr],
                "in_trade": (
                    meter_display_ids.get(trades.get(addr, None), "")
                    if addr in trades
                    else None
                ),
            }
            for addr in results
        ]
        return {
            "time": t.strftime("%H:%M:%S"),
            "meters": meters,
            "grid_state": fmt_grid_state(grid_state),
        }

    return moment

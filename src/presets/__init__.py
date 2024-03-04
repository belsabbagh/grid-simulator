
import pickle
import socket
import threading
from src.config import DEVIATION
from src.core.data_generator import mk_grid_state_generator, mk_instance_generator
from src.core.util import fmt_grid_state


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
        offers = list(
            {addr: results[addr] for addr in results if results[addr] > 0}.items()
        )
        trades = {}
        run_phase(conns, trade_connection, (offers, trades))
        trades = {k: v for k, v in trades.items() if v is not None}
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

import datetime
import socket
import threading
import time
import pickle

from src.core.util import date_range
from src.core.data_generator import mk_instance_generator
from config import (
    DEVIATION,
    START_DATE,
    END_DATE,
    UI_ADDRESS,
    NUM_HOUSES,
    INCREMENT_MINUTES,
    REFRESH_RATE,
    SERVER_ADDRESS,
)

data_generator = mk_instance_generator(DEVIATION)


def surplus_connection(conn, addr, t, results):
    gen, con = data_generator(t)
    conn.sendall(pickle.dumps({"type": "power", "generation": gen, "consumption": con}))
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


def moment(
    t, conns: list[tuple[socket.socket, tuple[str, int]]], ui_conn: socket.socket
):
    results: dict[tuple[str, int], float] = {}
    run_phase(conns, surplus_connection, (t, results))
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
    ui_update = {
        "time": t.strftime("%H:%M:%S"),
        "meters": meters,
    }
    ui_conn.sendall(pickle.dumps(ui_update))


if __name__ == "__main__":
    ui_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ui_conn.connect(UI_ADDRESS)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(SERVER_ADDRESS)
        s.listen(NUM_HOUSES)
        print("Server started")
        conns: list[tuple[socket.socket, tuple[str, int]]] = []
        print("Waiting to connect to meters...")
        for _ in range(NUM_HOUSES):
            conn, addr = s.accept()
            conns.append((conn, addr))
        for t in date_range(
            START_DATE, END_DATE, datetime.timedelta(minutes=INCREMENT_MINUTES)
        ):
            moment(t, conns, ui_conn)
            t += datetime.timedelta(minutes=INCREMENT_MINUTES)
            time.sleep(REFRESH_RATE)

import datetime
import socket
import threading
import time
import pickle
from src.core.data_generator import mk_instance_generator

INCREMENT_MINUTES = 1
REFRESH_RATE = 1
NUM_HOUSES = 20
SERVER_ADDRESS = ("localhost", 9405)
UI_ADDRESS = ("localhost", 7283)
START_DATE = datetime.datetime(2010, 1, 1, 10, 0, 0)
END_DATE = datetime.datetime(2010, 1, 1, 19, 0, 0)
DEVIATION = 0.1

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
    threads: list[threading.Thread] = []
    results: dict[tuple[str, int], float] = {}
    run_phase(conns, surplus_connection, (t, results))
    offers = list({addr: results[addr] for addr in results if results[addr] > 0}.items())
    trades = {}
    run_phase(conns, trade_connection, (offers, trades))
    trades = {k: v for k, v in trades.items() if v is not None}
    ui_update = {
        "type": "update",
        "time": t.strftime("%H:%M:%S"),
        "meters": results,
        "trades": trades,
    }
    ui_conn.sendall(pickle.dumps(ui_update))
    print(results)


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
        t = START_DATE
        while t < END_DATE:
            moment(t, conns, ui_conn)
            t += datetime.timedelta(minutes=INCREMENT_MINUTES)
            time.sleep(REFRESH_RATE)

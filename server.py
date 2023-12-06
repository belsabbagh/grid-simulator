import datetime
import socket
import threading
import time
import pickle
from src.core.data_generator import make_instance_generator
from src.core.msg_types import UIUpdate

INCREMENT_MINUTES = 1
REFRESH_RATE = 1
NUM_HOUSES = 12
SERVER_ADDRESS = ("localhost", 1234)
UI_ADDRESS = ("localhost", 1235)
START_DATE = datetime.datetime(2010, 1, 1, 10, 0, 0)
END_DATE = datetime.datetime(2010, 1, 1, 19, 0, 0)
DEVIATION = 0.1

data_generator = make_instance_generator(DEVIATION)


def client_connection(conn, addr, results):
    print(f"Connected by {addr}")
    gen, con = data_generator(t)
    conn.sendall(pickle.dumps({"type": "power", "generation": gen, "consumption": con}))
    data = pickle.loads(conn.recv(1024))
    results[addr] = data["surplus"]


def moment(
    t, conns: list[tuple[socket.socket, tuple[str, int]]], ui_conn: socket.socket
):
    print(f"Time: {t}")
    threads: list[threading.Thread] = []
    results: dict[tuple[str, int], float] = {}
    for conn, addr in conns:
        t1 = threading.Thread(target=client_connection, args=(conn, addr, results))
        t1.start()
        threads.append(t1)
    print("Threads started")
    for t1 in threads:
        t1.join()
    print("Threads finished")
    ui_update: UIUpdate = {
        "type": "update",
        "time": t.strftime("%H:%M:%S"),
        "meters": results,
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

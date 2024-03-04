import socket
import threading
import time
import pickle
import socket

from src.core.util import date_range
from src.core.meter import mk_meters_runner

def mksocket() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def make_simulation_server(n, server_address, ui_address):
    ui_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ui_conn.connect(ui_address)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(server_address)
        s.listen(n)
        print("Server started")
        conns: list[tuple[socket.socket, tuple[str, int]]] = []
        print("Waiting to connect to meters...")
        meters_runner = mk_meters_runner(n, server_address)
        meters_thread = threading.Thread(target=meters_runner)
        meters_thread.start()
        for _ in range(n):
            conn, addr = s.accept()
            conns.append((conn, addr))

    def simulate(start_date, end_date, datetime_delta, refresh_rate, moment):
        for t in date_range(start_date, end_date, datetime_delta):
            state = moment(t, conns)
            ui_conn.sendall(pickle.dumps(state))
            time.sleep(refresh_rate)

    return simulate

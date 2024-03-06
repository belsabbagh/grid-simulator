import pickle
import socket
import threading
import time
import socket
from src.config import DEVIATION
from src.core.comms import connect_sockets, make_msg_body
from src.core.data_generator import mk_grid_state_generator, mk_instance_generator
from src.core.meter import mk_meter, mk_meters_handler
from src.core.optimizer import mk_choose_best_offers_function

from src.core.util import date_range
from src.presets import mk_meters_runner

def make_simulation_server(n, server_address, append_state):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(server_address)
        s.listen(n)
        print("Server started")
        conns: list[tuple[socket.socket, tuple[str, int]]] = []
        print("Waiting to connect to meters...")
        meters_runner = mk_meters_runner(n, server_address)
        meters_thread = threading.Thread(target=meters_runner)
        meters_thread.daemon = True
        meters_thread.start()
        for _ in range(n):
            conn, addr = s.accept()
            conns.append((conn, addr))

    def simulate(start_date, end_date, datetime_delta, refresh_rate, moment):
        for t in date_range(start_date, end_date, datetime_delta):
            state = moment(t, conns)
            print(f"Moment {t} has passed.")
            append_state(state)
            time.sleep(refresh_rate)

    return simulate


def make_persistent_simulation_server(n, server_address, append_state):
    trade_chooser = mk_choose_best_offers_function(
        "models/grid-loss.h5",
        "models/duration.h5",
        "models/grid-loss.h5",
    )
    sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(n)]
    connect_sockets(sockets, server_address)
    sockets_dict = {
        s.getsockname(): mk_meter(s, None, None, None, trade_chooser) for s in sockets
    }
    start_threads, join_threads, fetch_state = mk_meters_handler(sockets_dict)

    def periodic_fetch_state():
        while True:
            append_state(fetch_state())

    fetch_state_thread = threading.Thread(target=periodic_fetch_state)

    data_generator = mk_instance_generator(DEVIATION)
    grid_state_generator = mk_grid_state_generator()

    def simulate(start_date, end_date, datetime_delta, refresh_rate):
        fetch_state_thread.start()
        for t in date_range(start_date, end_date, datetime_delta):
            grid_state = grid_state_generator(t)
            for s in sockets:
                gen, con = data_generator(t)
                msg = make_msg_body(
                    s.getsockname(),
                    "power",
                    datetime=t,
                    grid_state=grid_state,
                    generation=gen,
                    consumption=con,
                )
                s.sendall(pickle.dumps(msg))
                time.sleep(refresh_rate)

    return simulate

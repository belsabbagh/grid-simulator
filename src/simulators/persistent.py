import pickle
import socket
import threading
import datetime as dt
import time
import socket
from src.config import DEVIATION
from src.types import SimulateFunction
from src.core.util import date_range
from src.core.util.comms import connect_sockets, make_msg_body
from src.core.data_generator import mk_grid_state_generator, mk_instance_generator
from src.core.meter import mk_meter, mk_meters_handler
from src.core.optimizer import mk_choose_best_offers_function


def make_simulate(
    n, server_address, append_state
) -> SimulateFunction:
    trade_chooser = mk_choose_best_offers_function(
        "models/grid-loss.h5",
        "models/duration.h5",
        "models/grid-loss.h5",
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(server_address)
        s.listen(n)
        print("Server started. Waiting to connect to meters...")
        sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(n)]
        connect_sockets(sockets, server_address)
        sockets_dict = {
            s.getsockname(): mk_meter(s, None, None, None, trade_chooser)
            for s in sockets
        }
        start_threads, join_threads, fetch_state = mk_meters_handler(sockets_dict)

    def periodic_fetch_state():
        while True:
            append_state(fetch_state())

    fetch_state_thread = threading.Thread(target=periodic_fetch_state)

    def simulate(start_date, end_date, datetime_delta, refresh_rate):
        grid_state_generator = mk_grid_state_generator()
        data_generator = mk_instance_generator(
            start_date, end_date, datetime_delta, DEVIATION
        )
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

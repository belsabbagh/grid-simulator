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

from src.core.util import date_range, fmt_grid_state
from src.presets import mk_meters_runner


def send_and_recv_thread(conn, addr, message, result, results_loader, buf_size):
    conn.sendall(message)
    result[addr] = results_loader(conn.recv(buf_size))

def send_and_recv(conns_addrs, messages, results, results_loader, buf_size=1024):
    threads = []
    for conn, addr in conns_addrs:
        thread = threading.Thread(target=send_and_recv_thread, args=(conn, addr, messages[addr], results, results_loader, buf_size))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
        
def send_and_recv_sync(conns_addrs, messages, results, results_loader, buf_size=1024):
    for conn, addr in conns_addrs:
        conn.sendall(messages[addr])
        results[addr] = results_loader(conn.recv(buf_size))

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

    def simulate(start_date, end_date, datetime_delta, refresh_rate):
        data_generator = mk_instance_generator(
            start_date, end_date, datetime_delta, DEVIATION
        )
        grid_state_generator = mk_grid_state_generator()
        for t in date_range(start_date, end_date, datetime_delta):
            grid_state = grid_state_generator(t)
            results: dict[tuple[str, int], float] = {}
            messages = {}
            for _, addr in conns:
                gen, con = data_generator(t)
                messages[addr] = pickle.dumps(make_msg_body(
                    addr,
                    "power",
                    datetime=t,
                    grid_state=grid_state,
                    generation=gen,
                    consumption=con,
                ))
            send_and_recv_sync(conns, messages, results, lambda x: pickle.loads(x)['surplus'])
            offers = [
                {"source": addr, "amount": results[addr], "participation_count": 1}
                for addr in results
                if results[addr] > 0
            ]
            messages = {}
            for _, addr in conns:
                messages[addr] = pickle.dumps(make_msg_body(addr, "offers", offers=offers))
            trades = {}
            send_and_recv_sync(conns, messages, trades, lambda x: pickle.loads(x)['trade'])
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
            print(f"Moment {t} has passed.")
            append_state(
                {
                    "time": t.strftime("%H:%M:%S"),
                    "meters": meters,
                    "grid_state": fmt_grid_state(grid_state),
                }
            )
            time.sleep(refresh_rate)

    return simulate


def make_persistent_simulation_server(n, server_address, append_state):
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


def make_datagen_sim(n, _, append_state):
    ids = range(1, n + 1)

    def simulate(start_date, end_date, datetime_delta, refresh_rate):
        data_generator = mk_instance_generator(
            start_date, end_date, datetime_delta, DEVIATION
        )
        grid_state_generator = mk_grid_state_generator()
        for t in date_range(start_date, end_date, datetime_delta):
            grid_state = grid_state_generator(t)
            append_state(
                {
                    "time": t,
                    "grid_state": grid_state,
                    "meters": [
                        {
                            "id": f"{i}",
                            "generation": gen,
                            "consumption": con,
                        }
                        for i, (gen, con) in zip(ids, [data_generator(t) for _ in ids])
                    ],
                }
            )
            print(f"Moment {t} has passed.")
            time.sleep(refresh_rate)

    return simulate

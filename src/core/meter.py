import threading
import socket
import pickle

from src.core.util.comms import make_msg_body, make_sockets_handler, listen_for_duration
from src.types import SocketAddress


def mk_meter(
    s: socket.socket, dht_nodes_iter, blockchain_record, blockchain_fetch, trade_chooser
):
    meter_addr = s.getsockname()
    dt = None
    surplus = 0
    grid_state = [0, 0, 0, 0]
    trade = None

    def _handle_input(data):
        nonlocal dt, surplus, grid_state
        dt = data["datetime"]
        surplus = data["generation"] - data["consumption"]
        grid_state = data["grid_state"]

    def _broadcast_surplus():
        pass

    def _choose_offer():
        offers = []  # offers will be fetched from the dht
        result = trade_chooser(surplus, offers, grid_state)
        add_conn, _, send_to, _, _, concurrent_recv, _ = make_sockets_handler()
        for offer, fitness in result:
            addr = offer["source"]
            add_conn(addr)
            send_to(addr, make_msg_body(meter_addr, "power_request", fitness=fitness))
        response, msg = concurrent_recv(1024, 10)
        if response is not None:
            if msg["status"] == "accept":
                return offer

    def _handle_requests():
        """Receive requests from other meters."""
        messages = listen_for_duration(s, 1024, 10)
        sockets_index = {c.getpeername(): c for c in messages.keys()}
        _, close, send_to, _, sockets_iter, _, _ = make_sockets_handler(sockets_index)
        requests = {c.getpeername(): pickle.loads(messages[c]) for c in messages}
        conn = max(requests, key=lambda x: requests[x]["fitness"])
        send_to(conn, make_msg_body(meter_addr, "power_response", status="accept"))
        close(conn)
        for addr, c in sockets_iter():
            if c.fileno() == -1:
                continue
            send_to(addr, make_msg_body(meter_addr, "power_response", status="reject"))
            c.close()

    def _handle_surplus_positive():
        _broadcast_surplus()
        _handle_requests()

    def _handle_trade(source: SocketAddress):
        nonlocal trade
        trade = source

    def _handle_surplus_negative():
        offer = _choose_offer()
        if offer is not None:
            _handle_trade(offer["source"])

    surplus_handlers = [_handle_surplus_negative, _handle_surplus_positive]

    def _handle_surplus():
        while True:
            surplus_handlers[int(surplus > 0)]()

    def _listen_for_input():
        while True:
            data = pickle.loads(s.recv(1024))
            if data["type"] == "power":
                _handle_input(data)

    def _fetch_state():
        return {
            "timestamp": dt,
            "address": meter_addr,
            "surplus": surplus,
            "trade": trade,
        }

    def meter() -> None:
        input_thread = threading.Thread(target=_listen_for_input)
        input_thread.start()
        surplus_thread = threading.Thread(target=_handle_surplus)
        surplus_thread.start()

    return meter, _fetch_state


def mk_meters_handler(meters_dict):
    def get_start(addr):
        return meters_dict[addr][0]

    threads = [threading.Thread(target=get_start(addr)) for addr in meters_dict]

    def get_fetch_state_fn(addr):
        return meters_dict[addr][1]

    def start_threads():
        for t in threads:
            t.start()

    def join_threads():
        for t in threads:
            t.join()

    def fetch_state():
        return {addr: get_fetch_state_fn(addr)() for addr in meters_dict}

    return start_threads, join_threads, fetch_state

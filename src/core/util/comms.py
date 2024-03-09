import pickle
import select
import socket
import threading
import time
from typing import Iterable

from pyparsing import Any

def send_and_recv_thread(conn, addr, message, result, results_loader, buf_size):
    conn.sendall(message)
    result[addr] = results_loader(conn.recv(buf_size))


def send_and_recv_async(conns_addrs, messages, results, results_loader, buf_size=1024):
    """Warning! This function breaks when the number of connections is too high."""
    threads = []
    for conn, addr in conns_addrs:
        thread = threading.Thread(
            target=send_and_recv_thread,
            args=(conn, addr, messages[addr], results, results_loader, buf_size),
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def send_and_recv_sync(conns_addrs, messages, results, results_loader, buf_size=1024):
    for conn, addr in conns_addrs:
        conn.sendall(messages[addr])
        results[addr] = results_loader(conn.recv(buf_size))


def connect_sockets(sockets, addr):
    try:
        for s in sockets:
            s.connect(addr)
    except ConnectionRefusedError as e:
        raise ConnectionRefusedError(
            f"Socket {s.getsockname()} failed to connect to {addr}."
        ) from e


def connect_to(addr: tuple[str, int]) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    return s


def close_connection(s: socket.socket):
    s.close()


def send_data(s: socket.socket, data: Any):
    s.sendall(pickle.dumps(data))


def recv_data(s: socket.socket, buf_size: int, timeout: int) -> Any:
    s.settimeout(timeout)
    recv_stream: bytes = s.recv(buf_size)
    return pickle.loads(recv_stream)


def listen_for_duration(
    s: socket.socket, buf_size: int, duration: int
) -> dict[socket.socket, bytes]:
    messages = {}
    start_time = time.time()
    end_time = start_time + duration
    while time.time() < end_time:
        conn, _ = s.accept()
        messages[conn] = conn.recv(buf_size)
    return messages


def concurrent_recv(sockets: Iterable[socket.socket], buf_size: int, timeout: int):
    """
    Takes a list of sockets and listens to them in parallel.
    It stops on the first message received from any of the sockets.
    """
    received_data = {s: b"" for s in sockets}
    ready_to_read = list(sockets)

    while True:
        readable, _, _ = select.select(ready_to_read, [], [], timeout)

        if readable:
            for s in readable:
                data = s.recv(buf_size)
                received_data[s] += data
                if data:
                    return s, received_data[s]

        ready_to_read = [s for s in ready_to_read if s not in readable]
        if timeout == 0:
            return None, None


def concurrent_recv_duration(
    sockets: Iterable[socket.socket], buf_size: int, duration: int
):
    """
    Takes a list of sockets and listens to them in parallel for a specified duration.
    It reads from all sockets during the specified duration and returns the received data.
    """
    received_data = {s: b"" for s in sockets}
    ready_to_read = list(sockets)

    start_time = time.time()
    end_time = start_time + duration

    while time.time() < end_time:
        readable, _, _ = select.select(ready_to_read, [], [], end_time - time.time())

        if readable:
            for s in readable:
                data = s.recv(buf_size)
                received_data[s] += data

        ready_to_read = [s for s in ready_to_read if s not in readable]

    return received_data


def make_sockets_handler(init=None):
    sockets: dict[tuple[str, int], socket.socket] = init or {}

    def _connect_to(addr: tuple[str, int]) -> None:
        s = connect_to(addr)
        sockets[addr] = s

    def _close_connection(addr: tuple[str, int]) -> None:
        s = sockets[addr]
        close_connection(s)
        del sockets[addr]

    def _send_data(addr: tuple[str, int], data: Any) -> None:
        s = sockets[addr]
        send_data(s, data)

    def _recv_data(addr: tuple[str, int], buf_size: int, timeout: int) -> Any:
        s = sockets[addr]
        return recv_data(s, buf_size, timeout)

    def sockets_iterator():
        yield from sockets.items()

    def _concurrent_recv(buf_size: int, timeout: int) -> tuple[tuple[str, int], Any]:
        s, data = concurrent_recv(
            map(lambda x: x[1], sockets_iterator()), buf_size, timeout
        )
        addr = next(addr for addr, sock in sockets.items() if sock == s)
        return addr, data

    def _concurrent_recv_duration(
        buf_size: int, duration: int
    ) -> dict[tuple[str, int], Any]:
        received_data = concurrent_recv_duration(
            map(lambda x: x[1], sockets_iterator()), buf_size, duration
        )
        return {s.getpeername(): data for s, data in received_data.items()}

    return (
        _connect_to,
        _close_connection,
        _send_data,
        _recv_data,
        sockets_iterator,
        _concurrent_recv,
        _concurrent_recv_duration,
    )


def make_msg_body(addr, _type, **kwargs):
    return {"from": addr, "type": _type, **kwargs}

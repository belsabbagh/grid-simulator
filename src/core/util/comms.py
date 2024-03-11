"""This module contains utility functions for socket communication."""
import pickle
import select
import socket
import threading
import time
from typing import Any, Callable, Generator, Iterable, Optional, Tuple, Dict

from pyparsing import C, Any as PyparsingAny


def send_and_recv_thread(
    conn: socket.socket,
    addr: Tuple[str, int],
    message: bytes,
    result: Dict[Tuple[str, int], Any],
    results_loader: Any,
    buf_size: int,
) -> None:
    """Send a message to a socket, receive response, and store it in the result dictionary.

    Args:
        conn (socket.socket): The socket connection.
        addr (Tuple[str, int]): The address of the socket.
        message (bytes): The message to be sent.
        result (Dict[Tuple[str, int], Any]): The dictionary to store the received result.
        results_loader (Any): The function to load the received data.
        buf_size (int): The buffer size for receiving data.
    """
    conn.sendall(message)
    result[addr] = results_loader(conn.recv(buf_size))


def send_and_recv_async(
    conns_addrs: Iterable[Tuple[socket.socket, Tuple[str, int]]],
    messages: Dict[Tuple[str, int], bytes],
    results: Dict[Tuple[str, int], Any],
    results_loader: Any,
    buf_size: int = 1024,
) -> None:
    """Send messages to multiple sockets asynchronously and receive responses.

    Args:
        conns_addrs (Iterable[Tuple[socket.socket, Tuple[str, int]]]): Iterable of socket connections and addresses.
        messages (Dict[Tuple[str, int], bytes]): Dictionary mapping addresses to messages.
        results (Dict[Tuple[str, int], Any]): Dictionary to store received results.
        results_loader (Any): The function to load the received data.
        buf_size (int, optional): The buffer size for receiving data. Defaults to 1024.
    """
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


def send_and_recv_sync(
    conns_addrs: Iterable[Tuple[socket.socket, Tuple[str, int]]],
    messages: Dict[Tuple[str, int], bytes],
    results: Dict[Tuple[str, int], Any],
    results_loader: Any,
    buf_size: int = 1024,
) -> None:
    """Send messages to multiple sockets synchronously and receive responses.

    Args:
        conns_addrs (Iterable[Tuple[socket.socket, Tuple[str, int]]]): Iterable of socket connections and addresses.
        messages (Dict[Tuple[str, int], bytes]): Dictionary mapping addresses to messages.
        results (Dict[Tuple[str, int], Any]): Dictionary to store received results.
        results_loader (Any): The function to load the received data.
        buf_size (int, optional): The buffer size for receiving data. Defaults to 1024.
    """
    for conn, addr in conns_addrs:
        conn.sendall(messages[addr])
        results[addr] = results_loader(conn.recv(buf_size))


def connect_sockets(sockets: Iterable[socket.socket], addr: Tuple[str, int]) -> None:
    """Connect a list of sockets to the specified address.

    Args:
        sockets (Iterable[socket.socket]): Iterable of socket connections.
        addr (Tuple[str, int]): The address to connect to.
    """
    try:
        for s in sockets:
            s.connect(addr)
    except ConnectionRefusedError as e:
        raise ConnectionRefusedError(
            f"Socket {s.getsockname()} failed to connect to {addr}."
        ) from e


def connect_to(addr: Tuple[str, int]) -> socket.socket:
    """Connect to a socket at the specified address.

    Args:
        addr (Tuple[str, int]): The address to connect to.

    Returns:
        socket.socket: The connected socket.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    return s


def close_connection(s: socket.socket) -> None:
    """Close the connection of a socket.

    Args:
        s (socket.socket): The socket to close.
    """
    s.close()


def send_data(s: socket.socket, data: Any) -> None:
    """Send data through a socket.

    Args:
        s (socket.socket): The socket to send data through.
        data (Any): The data to send.
    """
    s.sendall(pickle.dumps(data))


def recv_data(s: socket.socket, buf_size: int, timeout: int) -> Any:
    """Receive data from a socket.

    Args:
        s (socket.socket): The socket to receive data from.
        buf_size (int): The buffer size for receiving data.
        timeout (int): The timeout duration for receiving data.

    Returns:
        Any: The received data.
    """
    s.settimeout(timeout)
    recv_stream: bytes = s.recv(buf_size)
    return pickle.loads(recv_stream)


def listen_for_duration(
    s: socket.socket, buf_size: int, duration: int
) -> Dict[socket.socket, bytes]:
    """Listen for connections for a specified duration.

    Args:
        s (socket.socket): The socket to listen on.
        buf_size (int): The buffer size for receiving data.
        duration (int): The duration to listen for connections.

    Returns:
        Dict[socket.socket, bytes]: Dictionary mapping sockets to received data.
    """
    messages = {}
    start_time = time.time()
    end_time = start_time + duration
    while time.time() < end_time:
        conn, _ = s.accept()
        messages[conn] = conn.recv(buf_size)
    return messages


def concurrent_recv(
    sockets: Iterable[socket.socket], buf_size: int, timeout: int
) -> Tuple[Optional[socket.socket], Optional[bytes]]:
    """Receive data from multiple sockets concurrently.

    Args:
        sockets (Iterable[socket.socket]): Iterable of sockets to receive data from.
        buf_size (int): The buffer size for receiving data.
        timeout (int): The timeout duration for receiving data.

    Returns:
        Tuple[Optional[socket.socket], Optional[bytes]]: The socket from which data is received and the received data.
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
) -> Dict[Tuple[str, int], bytes]:
    """Receive data from multiple sockets concurrently for a specified duration.

    Args:
        sockets (Iterable[socket.socket]): Iterable of sockets to receive data from.
        buf_size (int): The buffer size for receiving data.
        duration (int): The duration to receive data.

    Returns:
        Dict[Tuple[str, int], bytes]: Dictionary mapping socket addresses to received data.
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

    return {s.getpeername(): data for s, data in received_data.items()}


ConnectTo = Callable[[Tuple[str, int]], socket.socket]
CloseConnection = Callable[[Tuple[str, int]], None]
SendData = Callable[[Tuple[str, int], Any], None]
RecvData = Callable[[Tuple[str, int], int, int], Any]
SocketsIterator = Generator[Tuple[Tuple[str, int], socket.socket], None, None]
ConcurrentRecv = Callable[[int, int], Tuple[Tuple[str, int], Optional[bytes]]]
ConcurrentRecvDuration = Callable[[int, int], Dict[Tuple[str, int], bytes]]


def make_sockets_handler(
    init: Optional[Dict[Tuple[str, int], socket.socket]] = None
) -> Tuple[
    ConnectTo,
    CloseConnection,
    SendData,
    RecvData,
    Callable[[], SocketsIterator],
    ConcurrentRecv,
    ConcurrentRecvDuration,
]:
    """Create a handler for socket operations."""
    sockets: Dict[Tuple[str, int], socket.socket] = init or {}

    def _connect_to(addr: Tuple[str, int]) -> socket.socket:
        s = connect_to(addr)
        sockets[addr] = s
        return s

    def _close_connection(addr: Tuple[str, int]) -> None:
        s = sockets[addr]
        close_connection(s)
        del sockets[addr]

    def _send_data(addr: Tuple[str, int], data: Any) -> None:
        s = sockets[addr]
        send_data(s, data)

    def _recv_data(addr: Tuple[str, int], buf_size: int, timeout: int) -> Any:
        s = sockets[addr]
        return recv_data(s, buf_size, timeout)

    def sockets_iterator() -> (
        Generator[Tuple[Tuple[str, int], socket.socket], None, None]
    ):
        yield from sockets.items()

    def _concurrent_recv(
        buf_size: int, timeout: int
    ) -> Tuple[Tuple[str, int], Optional[bytes]]:
        s, data = concurrent_recv(
            map(lambda x: x[1], sockets_iterator()), buf_size, timeout
        )
        addr = next(addr for addr, sock in sockets.items() if sock == s)
        return addr, data

    def _concurrent_recv_duration(
        buf_size: int, duration: int
    ) -> Dict[Tuple[str, int], bytes]:
        received_data = concurrent_recv_duration(
            map(lambda x: x[1], sockets_iterator()), buf_size, duration
        )
        return {s: data for s, data in received_data.items()}

    return (
        _connect_to,
        _close_connection,
        _send_data,
        _recv_data,
        sockets_iterator,
        _concurrent_recv,
        _concurrent_recv_duration,
    )

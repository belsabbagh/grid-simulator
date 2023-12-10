import socket
import threading
from typing import Literal
from src.core.meter import Meter

N = 12
BUFFER_SIZE = 512
SERVER_ADDRESS: tuple[Literal["localhost"], Literal[1234]] = ("localhost", 1234)


def mksocket() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


if __name__ == "__main__":
    meters: list[Meter] = [
        Meter(mksocket(), SERVER_ADDRESS, BUFFER_SIZE) for _ in range(N)
    ]
    while True:
        threads = [m.mkthread() for m in meters]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("Iteration finished")

import socket
from src.core.meter import Meter
N = 12
BUFFER_SIZE = 512
SERVER_ADDRESS = ("localhost", 1234)

if __name__ == "__main__":
    meters = [Meter(socket.socket(socket.AF_INET, socket.SOCK_STREAM), SERVER_ADDRESS, BUFFER_SIZE) for _ in range(N)]
    while True:
        threads = [m.create_thread() for m in meters]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("Iteration finished")

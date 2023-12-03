import pickle
import socket
import sys
import threading

N = 12
BUFFER_SIZE = 170
SERVER_ADDRESS = ("localhost", 1234)

def process(data):
    """This is where the magic happens"""
    gen, con = data
    return float(gen) - float(con)

def client_thread(s):
    data = s.recv(BUFFER_SIZE)
    print(f"Received {sys.getsizeof(data)} bytes from {s.getpeername()}")
    if not data:
        return
    data = pickle.loads(data)
    res = process(data)
    s.sendall(pickle.dumps(res))


if __name__ == "__main__":
    sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(N)]
    for s in sockets:
        s.connect(SERVER_ADDRESS)
    while True:
        threads = [threading.Thread(target=client_thread, args=(s,)) for s in sockets]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("Iteration finished")

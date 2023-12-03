import datetime
import socket
import threading
import time
import pickle
from src.core.data_generator import make_instance_generator

INCREMENT_MINUTES = 1
REFRESH_RATE = 1
NUM_HOUSES = 12
SERVER_ADDRESS = ("localhost", 1234)
START_DATE = datetime.datetime(2010, 1, 1, 10, 0, 0)
END_DATE = datetime.datetime(2010, 1, 1, 19, 0, 0)
DEVIATION = 0.1

data_generator = make_instance_generator(DEVIATION)

def client_connection(conn, addr, results):
    print(f"Connected by {addr}")
    instance = data_generator(t)
    conn.sendall(pickle.dumps(instance))
    data = pickle.loads(conn.recv(1024))
    results[addr] = data
    
def moment(t, conns):
    print(f"Time: {t}")
    threads = []
    results = {}
    for conn, addr in conns:
        t1 = threading.Thread(target=client_connection, args=(conn, addr, results))
        t1.start()
        threads.append(t1)
    print("Threads started")
    for t1 in threads:
        t1.join()
    print("Threads finished")
    print(results)

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(SERVER_ADDRESS)
        s.listen(NUM_HOUSES)
        print("Server started")
        conns = [s.accept() for _ in range(NUM_HOUSES)]
        t = START_DATE
        while t < END_DATE:
            moment(t, conns)
            t += datetime.timedelta(minutes=INCREMENT_MINUTES)
            time.sleep(REFRESH_RATE)
                
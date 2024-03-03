import socket
from src.core.meter import meter_mkthread
from src.core.optimizer import mk_choose_best_offers_function
from config import SERVER_ADDRESS, NUM_HOUSES

BUFFER_SIZE = 512


def mksocket() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


if __name__ == "__main__":
    trade_chooser = mk_choose_best_offers_function(
        "models/grid-loss.h5",
        "models/duration.h5",
        "models/grid-loss.h5",
    )
    sockets = [mksocket() for _ in range(NUM_HOUSES)]
    for s in sockets:
        s.connect(SERVER_ADDRESS)
    meters = [meter_mkthread(s, BUFFER_SIZE,trade_chooser) for s in sockets]
    while True:
        threads = [m() for m in meters]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("Iteration finished")

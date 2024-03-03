import socket
from src.core.data_service.dht import create_dht
from src.core.meter import Meter
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
    socket_addrs = [s.getsockname() for s in sockets]
    dht_get, dht_put_fns = create_dht(socket_addrs)
    meters = [
        Meter(s, BUFFER_SIZE, trade_chooser) for s, dht_put in zip(sockets, dht_put_fns)
    ]
    while True:
        threads = [m.mkthread() for m in meters]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("Iteration finished")

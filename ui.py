from typing import Callable, Literal
from src.gui import App, MainWindow
import socket
import threading
import pickle
from src.core.msg_types import UIUpdate

ADDRESS: tuple[Literal["localhost"], Literal[1235]] = ("localhost", 1235)
N = 12


def trade(window: MainWindow.GridView, msg: UIUpdate) -> None:
    return None


def no_update(_window: MainWindow.GridView, _msg: UIUpdate) -> None:
    return None


def update(window: MainWindow.GridView, msg: UIUpdate) -> None:
    window.update_timer_label(msg["time"])
    window.update_grid(msg["meters"])


ui_updates: dict[str, Callable[[MainWindow.GridView, UIUpdate], None]] = {
    "update": update,
    "trade": trade,
}


def update_ui(window: MainWindow.GridView, conn) -> None:
    while True:
        data: UIUpdate = pickle.loads(conn.recv(2048))
        ui_updates.get(data["type"], no_update)(window, data)


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(ADDRESS)
    s.listen()
    print("UI server started")
    print("Waiting for `server.py` to start...")
    conn, addr = s.accept()
    print(f"Connection from {addr} has been established!")
    data = pickle.loads(conn.recv(2048))
    meter_ids: list[tuple[str, int]] = [i for i in data["meters"].keys()]
    print(meter_ids)
    app = App(meter_ids)
    # grid.connect_all((240, 180, 255))
    threading = threading.Thread(target=update_ui, args=(app.window, conn))
    threading.start()
    app.exec()

import pickle
import socket
from config import WEB_UI_URL, UI_SERVER_ADDRESS
from src.server import create_flask_state_buffer, make_state_buffer


def make_collect_state(conn):
    def collect_state():
        while True:
            data = pickle.loads(conn.recv(2048))
            append_state(data)

    return collect_state


if __name__ == "__main__":
    append_state, fetch_next_state = make_state_buffer()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(UI_SERVER_ADDRESS)
        s.listen()
        print("UI server started")
        print("Waiting for server connection...")
        conn, addr = s.accept()
        print(f"Connection from {addr} has been established!")

    start_server = create_flask_state_buffer(
        WEB_UI_URL,
        make_collect_state(conn),
        fetch_next_state,
    )
    start_server()

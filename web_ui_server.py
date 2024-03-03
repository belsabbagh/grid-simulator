# create flask server to test the model

from flask import Flask, jsonify
from flask_cors import CORS
import threading
import socket
import pickle
from config import WEB_UI_URL, UI_SERVER_ADDRESS

app = Flask(__name__)
cors_options = {"origins": WEB_UI_URL}
cors = CORS(app, resources={r"/next": cors_options, r"/": cors_options})


def make_state_buffer():  # -> tuple[Callable[..., None], Callable[[], dict[str, Any]]]:
    buffer = []

    def append_state(state):
        buffer.append(state)

    def fetch_next_state():
        """pop the first state from the buffer"""
        if not buffer:
            return None
        state = buffer.pop(0)
        state["remaining"] = len(buffer)
        return state
    return append_state, fetch_next_state


append, fetch = make_state_buffer()


def collect_state(conn):
    while True:
        data = pickle.loads(conn.recv(2048))
        append(data)


@app.route("/next", methods=["GET"])
def _():
    state = fetch()
    return jsonify(state)


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(UI_SERVER_ADDRESS)
        s.listen()
        print("UI server started")
        print("Waiting for `server.py` to start...")
        conn, addr = s.accept()
        print(f"Connection from {addr} has been established!")
    threading = threading.Thread(target=collect_state, args=(conn,))
    threading.start()
    app.run()

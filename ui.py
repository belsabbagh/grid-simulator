from src.gui import App
import socket
import threading
import pickle

ADDRESS = ("localhost", 1235)
N = 12

def update_ui(window, conn):
    grid = window.grid
    time = window.timer
    while True:
        data = pickle.loads(conn.recv(2048))
        data_type = data["type"]
        match data_type:
            case "trade":
                from_meter = data["from_meter"]
                to_meter = data["to_meter"]
                grid.connect(from_meter, to_meter, (0, 0, 0))
            case "update":
                time.setText(data["time"])
                for meter_id, meter_data in data["meters"].items():
                    surplus = meter_data
                    grid.set_text_meter(meter_id, str(round(surplus, 2)))
                    grid.color_meter(meter_id, (0, 255, 0) if surplus > 0 else (255, 0, 0))
            case _:
                print("Invalid message type")
                
if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(ADDRESS)
        s.listen()
        print("UI server started")
        conn, addr = s.accept()
        print(f"Connection from {addr} has been established!")
        data = pickle.loads(conn.recv(2048))
        meter_ids = [i for i in data["meters"].keys()]
        print(meter_ids)
        app = App(meter_ids)
        grid = app.window.grid
        time = app.window.timer
        grid.connect_all((128, 64, 0))
        threading = threading.Thread(target=update_ui, args=(app.window, conn,  ))
        threading.start()
        app.exec()


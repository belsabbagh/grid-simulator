from src.gui import App
import socket
import threading
import asyncio

meter_ids = [str(i) for i in range(0, 12)]
app = App(meter_ids)


async def update_data(grid, time):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 1234))
    s.listen()
    while True:
        clientsocket, address = s.accept()
        print(f"Connection from {address} has been established!")
        msg = clientsocket.recv(1024)
        print(msg.decode("utf-8"))
        msg = eval(msg.decode("utf-8"))
        if msg["type"] == "update":
            if msg["time"]:
                time.setText(msg["time"])
            # if message is a meter_update, it will be a list from 0 to 12 with the consumption and generation of each meter
            # we will have to update the grid accordingly
            if msg["meter_update"]:
                for i in range(msg["meter_update"].__len__()):
                    generation = float(msg["meter_update"][i]["generation"])
                    consumption = float(msg["meter_update"][i]["consumption"])
                    difference = generation - consumption
                    grid.set_text_meter(str(i), str(round(difference, 2)))
                    if difference > 0:
                        grid.color_meter(str(i), (0, 255, 0))
                    else:
                        grid.color_meter(str(i), (255, 0, 0))
        if msg["type"] == "trade":
            from_meter = str(msg["from_meter"])
            to_meter = str(msg["to_meter"])
            print("from_meter: " + from_meter)
            print("to_meter: " + to_meter)
            grid.connect(from_meter, to_meter, (0, 0, 0))

def run_update_data(grid, time):
    asyncio.run(update_data(grid, time))

def main():
    grid = app.window.grid
    time = app.window.timer
    grid.connect_all((128, 64, 0))

    # run the update_data function in a thread
    # this function will run while true, will work as a server, that will receive data from any meter and the simulator, and will update the grid accordingly
    thread = threading.Thread(target=run_update_data, args=(grid, time))
    thread.start()
    app.exec()
    # thread.join()


if __name__ == "__main__":
    # grid = app.window.grid
    # time = app.window.timer
    # grid.connect_all((128, 64, 0))
    # # grid.color_meter("1", (0, 255, 0))
    # grid.color_meter("1", (0, 255, 0))
    # grid.set_text_meter("1", "100")
    # time.setText("00:01")
    # grid.connect("1", "6", (255, 0, 0))
    # app.exec()
    main()

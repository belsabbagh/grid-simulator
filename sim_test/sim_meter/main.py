import threading
import socket

class Meter:
    def __init__(self, meter_id):
        self.meter_id = meter_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 5000))
        self.socket.sendall(bytes(str(self.meter_id), "utf-8"))
        self.port = eval(self.socket.recv(1024).decode("utf-8"))["init_port"]
        self.consumption = 0
        self.generated = 0
        self.taken = 0
        self.given = 0
        self.status = "none"
        self.log = {}
        self.curr_epoch = 0
        self.curr_log = {}
        self.curr_actions = []

    def update_metrics(self, data):
        self.consumption = data["consumption"]
        self.generated = data["generated"]

    def detect_power_consumption(self):
        print("Detecting power consumption")
        difference = (self.consumption + self.given) - (self.generated + self.taken)
        if difference > 0:
            print(f"House {self.meter_id} needs power")
            data = {"meter_id": self.meter_id, "power": difference}
            self.socket.sendall(bytes(str(data), "utf-8"))
            self.status = "deficit"

        elif difference < 0:
            print(f"House {self.meter_id} has surplus power")
            data = {"meter_id": self.meter_id, "power": difference}
            self.socket.sendall(bytes(str(data), "utf-8"))
            self.status = "surplus"

    def wait_for_power(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(("localhost", self.port))
            while True:
                server_socket.listen()
                conn, addr = server_socket.accept()
                data = conn.recv(1024)
                data = eval(data.decode("utf-8"))
                if not data:
                    break
                type = data["type"]
                if type == "power":
                    if self.status != "deficit":
                        return
                    amount = data["amount"]
                    meter_id = data["meter_id"]
                    print(f"Meter: {meter_id} sent {amount} power")
                    self.taken += amount
        except:
            pass

    def give_power(self, amount, ip, port):
        if self.status == "surplus":
            if amount > self.generated - self.consumption:
                print(f"Meter {self.meter_id} has {self.generated - self.consumption} power")
                amount = self.generated - self.consumption
            data = {"meter_id": self.meter_id, "amount": amount, "type": "power"}
            socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.connect((ip, port))
            socket.sendall(bytes(str(data), "utf-8"))
            self.given += amount

    def clear_for_next_epoch(self):
        self.taken = 0
        self.generated = 0
        self.consumption = 0
        self.given = 0
        self.status = "none"
        self.curr_actions = []


    def listen(self):
        while True:
            try:
                curr_action = "none"
                data = self.socket.recv(1024)
                data = eval(data.decode("utf-8"))

                if not data:
                    break

                print(f"Meter {self.meter_id} received data: {data}")

                if data["epoch"]:
                    if data["epoch"] != self.curr_epoch:
                        self.clear_for_next_epoch()
                        self.curr_epoch = data["epoch"]
                elif data["type"] == "give_power":
                    self.give_power(data["amount"], data["meter_id"], data["ip"], data["port"])
                    curr_action = "give_power"
                elif data["type"] == "update":
                    self.update_metrics(data)
                    curr_action = "update"

                print(f"Meter {self.meter_id}: Consumption: {self.consumption}, Generated: {self.generated}, Taken: {self.taken}")
                print(f"Meter {self.meter_id}: Current Actions: {self.curr_actions}")

                self.detect_power_consumption()
                self.curr_log = {"meter_id": self.meter_id, "consumption": self.consumption, "generated": self.generated, "taken": self.taken, "actions": self.curr_actions}
                self.curr_actions.append(curr_action)
                if self.curr_epoch in self.log:
                    self.curr_log["actions"] = self.log[self.curr_epoch]["actions"] + self.curr_log["actions"]
                    self.log[self.curr_epoch] = self.curr_log
                else:
                    self.log[self.curr_epoch] = self.curr_log
            except:
                continue

    def start(self):
        thread = threading.Thread(target=self.listen)
        thread2 = threading.Thread(target=self.wait_for_power)
        thread.start()
        thread2.start()
        return thread, thread2


if __name__ == "__main__":
    meter_list = []
    threads = []

    num_meters = 12
    for i in range(num_meters):
        meter = Meter(i)
        meter_list.append(meter)
        thread1, thread2 = meter.start()
        threads.extend([thread1, thread2])

    print(f"Started {num_meters} meters")

    for thread in threads:
        thread.join()

    print("All threads joined. Exiting.")


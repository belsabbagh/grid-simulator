import pickle
import threading
import socket
from typing import Any, Callable
import random


class Meter:
    s: socket.socket
    trade_chooser: Callable

    def __init__(
        self,
        s: socket.socket,
        buf_size: int,
        trade_chooser: Callable,
    ) -> None:
        self.s = s
        self.buffer_size = buf_size
        self.trade_chooser = trade_chooser

    def mkthread(self, args=None):
        if args is None:
            args = ()
        return threading.Thread(target=self.run, args=args)

    def run(self):
        recv_stream: bytes = self.s.recv(self.buffer_size)
        if not recv_stream:
            return
        data: dict[str, Any] = pickle.loads(recv_stream)
        data_type = data["type"]
        if data_type != "power":
            raise ValueError("Haven't received power data.")
        gen, con = data["generation"], data["consumption"]
        surplus = gen - con
        self.s.sendall(
            pickle.dumps(
                {"from": self.s.getsockname(), "surplus": surplus, type: "surplus"}
            )
        )
        recv_stream = self.s.recv(2048)
        if not recv_stream:
            return
        data = pickle.loads(recv_stream)
        if data["type"] != "offers":
            return
        if not data["offers"]:
            self.s.sendall(pickle.dumps({"from": self.s.getsockname(), "trade": None}))
            return
        if surplus > 0:
            self.s.sendall(pickle.dumps({"from": self.s.getsockname(), "trade": None}))

        source, amount = random.choice(data["offers"])
        self.s.sendall(pickle.dumps({"from": self.s.getsockname(), "trade": source}))

    def is_connected(self) -> bool:
        return self.s.fileno() != -1


class OldMeter:
    def __init__(self, meter_id):
        self.meter_id = meter_id
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("localhost", 5000))
        self.s.sendall(bytes(str(self.meter_id), "utf-8"))
        self.port = eval(self.s.recv(1024).decode("utf-8"))["init_port"]
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
            self.s.sendall(bytes(str(data), "utf-8"))
            self.status = "deficit"

        elif difference < 0:
            print(f"House {self.meter_id} has surplus power")
            data = {"meter_id": self.meter_id, "power": difference}
            self.s.sendall(bytes(str(data), "utf-8"))
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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        if self.status == "surplus":
            if amount > self.generated - self.consumption:
                print(
                    f"Meter {self.meter_id} has {self.generated - self.consumption} power"
                )
                amount = self.generated - self.consumption
            data = {"meter_id": self.meter_id, "amount": amount, "type": "power"}
            s.sendall(bytes(str(data), "utf-8"))
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
                data = self.s.recv(1024)
                data = eval(data.decode("utf-8"))

                if not data:
                    break

                print(f"Meter {self.meter_id} received data: {data}")

                if data["epoch"]:
                    if data["epoch"] != self.curr_epoch:
                        self.clear_for_next_epoch()
                        self.curr_epoch = data["epoch"]
                elif data["type"] == "give_power":
                    self.give_power(data["amount"], data["ip"], data["port"])
                    curr_action = "give_power"
                elif data["type"] == "update":
                    self.update_metrics(data)
                    curr_action = "update"

                print(
                    f"Meter {self.meter_id}: Consumption: {self.consumption}, Generated: {self.generated}, Taken: {self.taken}"
                )
                print(f"Meter {self.meter_id}: Current Actions: {self.curr_actions}")

                self.detect_power_consumption()
                self.curr_log = {
                    "meter_id": self.meter_id,
                    "consumption": self.consumption,
                    "generated": self.generated,
                    "taken": self.taken,
                    "actions": self.curr_actions,
                }
                self.curr_actions.append(curr_action)
                if self.curr_epoch in self.log:
                    self.curr_log["actions"] = (
                        self.log[self.curr_epoch]["actions"] + self.curr_log["actions"]
                    )
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

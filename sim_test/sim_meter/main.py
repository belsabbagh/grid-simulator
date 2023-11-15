import threading 
import socket 

class Meter: 
    def __init__(self, meter_id):
        self.meter_id = meter_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 5000))
        self.socket.sendall(bytes(str(self.meter_id), "utf-8"))
        self.consumption = 0
        self.generated = 0
        self.taken = 0
        self.status = "none"
        self.log = {}
        self.curr_epoch = 0
        self.curr_log = {}
    
    def update_metrics(self, data): 
        self.consumption = data["consumption"]
        self.generated = data["generated"]

    def detect_power_consumption(self):
        difference = self.consumption - (self.generated + self.taken)
        if difference > 0:
            print(f"House {self.meter_id} needs power")
            data = {"meter_id": self.meter_id, "power": difference}
            self.socket.sendall(bytes(str(data), "utf-8"))
            self.status = "deficit"

        elif difference < 0:
            print(f"House {self.meter_id} has excess power")
            data = {"meter_id": self.meter_id, "power": difference}
            self.socket.sendall(bytes(str(data), "utf-8"))
            self.status = "excess"

    def wait_for_power(self, data):
        if self.status != "deficit":
            return
        amount = data["amount"]
        meter_id = data["meter_id"]
        print(f"Meter: {meter_id} sent {amount} power")
        self.taken += amount

    def give_power(self, amount, ip, port):
        if self.status == "excess":
            if amount > self.generated - self.consumption:
                print(f"Meter {self.meter_id} has {self.generated - self.consumption} power")
                amount = self.generated - self.consumption
            data = {"meter_id": self.meter_id, "amount": amount, "type": "power"}
            socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.connect((ip, port))
            socket.sendall(bytes(str(data), "utf-8"))

    def clear_for_next_epoch(self):
        self.taken = 0
        self.generated = 0
        self.consumption = 0
        self.status = "none"


    def listen(self):
        while True:
            curr_action = "none"
            data = self.socket.recv(1024)
            data = eval(data.decode("utf-8"))
            if data["epoch"]: 
                if data["epoch"] != self.curr_epoch:
                    self.clear_for_next_epoch()
                    self.curr_epoch = data["epoch"]
            
            if data["type"] == "power":
                self.wait_for_power(data)
                curr_action = "get_power"
            elif data["type"] == "give_power":
                self.give_power(data["amount"], data["meter_id"], data["ip"], data["port"])
                curr_action = "give_power"
            elif data["type"] == "update":
                self.update_metrics(data)
                curr_action = "update"
            
            self.detect_power_consumption()
            self.curr_log = {"meter_id": self.meter_id, "consumption": self.consumption, "generated": self.generated, "taken": self.taken, "action": curr_action}
            self.log[self.curr_epoch] = self.curr_log

            

    def start(self):
        thread = threading.Thread(target=self.listen)
        thread.start()


if __name__ == "__main__":
    meter_list = []
    num_meters = 10
    for i in range(num_meters):
        meter = Meter(i)
        meter_list.append(meter)
        meter.start()
    print(f"Started {num_meters} meters")
    while True:
        pass
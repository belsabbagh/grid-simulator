import subprocess
import threading
from PyQt6 import QtWidgets


class TextView(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)

    def log(self, text):
        self.append(text)


class MainWindow(QtWidgets.QMainWindow):
    ui_log: TextView
    server_log: TextView
    clients_log: TextView

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logger")
        self.resize(1200, 800)
        frame = QtWidgets.QFrame()
        layout = QtWidgets.QHBoxLayout()
        frame.setLayout(layout)
        self.setCentralWidget(frame)
        self.ui_log = TextView()
        self.server_log = TextView()
        self.clients_log = TextView()
        layout.addWidget(self.ui_log)
        layout.addWidget(self.server_log)
        layout.addWidget(self.clients_log)
        self.show()


class BackendApp(QtWidgets.QApplication):
    def __init__(self):
        super().__init__([])
        self.main_window = MainWindow()


def update_logger(textview, p: subprocess.Popen):
    while True:
        if not p.stdout:
            continue
        line = p.stdout.readline()
        if not line:
            textview.log("Nothing to write\n")
        textview.log(line.decode("utf-8"))

if __name__ == "__main__":
    app = BackendApp()
    # start the 3 scripts
    subprocesses = [
        subprocess.Popen(["python", "server.py"], stdout=subprocess.PIPE),
        subprocess.Popen(["python", "clients.py"], stdout=subprocess.PIPE),
        subprocess.Popen(["python", "ui.py"], stdout=subprocess.PIPE),
    ]
    # read the output of each script and log it in the UI
    for p in subprocesses:
        textview = None
        name = p.args[1].split("\\")[-1]
        match name:
            case "server.py":
                textview = app.main_window.server_log
            case "clients.py":
                textview = app.main_window.clients_log
            case "ui.py":
                textview = app.main_window.ui_log
            case _:
                print(f"Invalid script name: {name}")
        threading.Thread(target=update_logger, args=(textview, p)).start()
    print("All scripts started")
    app.exec()

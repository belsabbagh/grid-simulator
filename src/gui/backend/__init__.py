from PyQt6 import QtWidgets

class TextView(QtWidgets.QTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)

    def log(self, text) -> None:
        self.append(text)


class MainWindow(QtWidgets.QMainWindow):
    ui_log: TextView
    server_log: TextView
    clients_log: TextView

    def __init__(self) -> None:
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
    def __init__(self) -> None:
        super().__init__([])
        self.main_window = MainWindow()

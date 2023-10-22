from PyQt6 import QtWidgets as QtW
from .MainWindow import MainWindow


class App(QtW.QApplication):
    def __init__(self, meter_ids):
        super().__init__([])
        self.window = MainWindow(meter_ids)
        self.window.show()


__all__ = ["App"]
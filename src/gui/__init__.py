from PyQt6 import QtWidgets as QtW
from .MainWindow import GridView as MW
from .MainWindow import TestPredict as TP


class App(QtW.QApplication):
    def __init__(self, meter_ids) -> None:
        super().__init__([])
        self.window = MW(meter_ids)
        self.window.show()

class PredictApp(QtW.QApplication):
    def __init__(self) -> None:
        super().__init__([])
        self.window = TP()
        self.window.show()

__all__ = ["App"]

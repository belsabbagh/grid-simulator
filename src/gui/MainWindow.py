from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import Qt
from .MetersGrid import MetersGrid
from .KeyValueList import KeyValueList


class GridView(QtW.QMainWindow):
    grid: MetersGrid
    timer: QtW.QLabel

    def __init__(self, meter_ids) -> None:
        super().__init__()
        self.setWindowTitle("Meters")
        self.setGeometry(100, 100, 1000, 600)
        self.grid = MetersGrid(meter_ids, 48)
        self.timer = QtW.QLabel()
        headerLayout: QtW.QVBoxLayout = self.__mk_header()  # type: ignore
        mainLayout = QtW.QHBoxLayout()
        mainWidget = QtW.QWidget()
        mainLayout.addLayout(headerLayout)
        mainLayout.addWidget(self.grid)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def __mk_header(self) -> QtW.QHBoxLayout:
        self.timer.setText("00:00")
        font = self.timer.font()
        font.setPointSize(24)
        self.timer.setFont(font)
        self.timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headerLayout = QtW.QHBoxLayout()
        headerLayout.addWidget(self.timer)
        return headerLayout

    def update_timer_label(self, text) -> None:
        self.timer.setText(text)

    def update_grid(self, meters) -> None:
        for meter_id, meter_data in meters.items():
            surplus: float = meter_data
            self.grid.set_text_meter(meter_id, str(round(surplus, 2)))
            self.grid.color_meter(meter_id, (0, 255, 0) if surplus > 0 else (255, 0, 0))


class TestPredict(QtW.QMainWindow):
    timer: QtW.QLabel
    parameters: KeyValueList
    predictions: KeyValueList

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TestPredict")
        self.setGeometry(100, 100, 1000, 600)
        self.timer = QtW.QLabel()
        headerLayout: QtW.QHBoxLayout = self.__mk_header()
        mainLayout = QtW.QHBoxLayout()
        mainWidget = QtW.QWidget()
        mainLayout.addLayout(headerLayout)
        self.parameters = KeyValueList(
            {
                "Grid load (GWh)": 0,
                "Grid temperature (C)": 0,
                "Voltage (V)": 0,
                "Global intensity (A)": 0,
                "Transaction amount (Wh)": 0,
            }
        )
        self.predictions = KeyValueList(
            {
                "Expected Efficiency": 0,
                "Expected Duration (hr)": 0,
            }
        )
        mainLayout.addWidget(self.parameters)
        mainLayout.addWidget(self.predictions)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def __mk_header(self) -> QtW.QHBoxLayout:
        self.timer.setText("00:00")
        font = self.timer.font()
        font.setPointSize(24)
        self.timer.setFont(font)
        self.timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headerLayout = QtW.QHBoxLayout()
        headerLayout.addWidget(self.timer)
        return headerLayout

    def update_timer_label(self, text) -> None:
        self.timer.setText(text)

    def update_parameters(self, data: dict) -> None:
        self.parameters.update(data)

    def update_predictions(self, data: dict) -> None:
        self.predictions.update(data)

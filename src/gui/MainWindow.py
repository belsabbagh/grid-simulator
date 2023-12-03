from PyQt6 import QtWidgets as QtW
import PyQt6 as Qt
from .MetersGrid import MetersGrid


class MainWindow(QtW.QMainWindow):
    grid: MetersGrid
    timer: QtW.QLabel

    def __init__(self, meter_ids):
        super().__init__()
        self.setWindowTitle("Meters")
        self.setGeometry(100, 100, 1000, 600)
        self.grid = MetersGrid(meter_ids, 48)
        self.timer = QtW.QLabel()
        headerLayout = self.__mk_header()
        mainLayout = QtW.QVBoxLayout()
        mainWidget = QtW.QWidget()
        mainLayout.addLayout(headerLayout)
        mainLayout.addWidget(self.grid)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def __mk_header(self):
        self.timer.setText("00:00")
        font = self.timer.font()
        font.setPointSize(24)
        self.timer.setFont(font)
        self.timer.setAlignment(Qt.QtCore.Qt.AlignmentFlag.AlignCenter)
        headerLayout = QtW.QHBoxLayout()
        headerLayout.addWidget(self.timer)
        return headerLayout

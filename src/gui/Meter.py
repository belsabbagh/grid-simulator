from PyQt6 import QtWidgets as QtW
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image, ImageQt
import PyQt6 as Qt


def color_icon(img: Image, color: tuple) -> Image:
    """Replace solid black pixels with a color"""
    data = img.getdata()
    img.putdata([color if px[-1] != 0 else px for px in data])
    return img


class Meter(QtW.QWidget):
    icon = None
    frame = None
    canvas = None
    meter_id = None
    text = None

    def __init__(self, meter_id, size=100):
        super().__init__()
        self.meter_id = meter_id
        self.img = Image.open("assets/meter.png").convert("RGBA").resize((size, size))
        qtimg = QImage(ImageQt.ImageQt(self.img))
        self.icon = QtW.QLabel()
        pixmap = QPixmap.fromImage(qtimg)
        self.icon.setPixmap(pixmap)
        self.text = QtW.QLabel()
        self.text.setText("0")
        self.text.setAlignment(Qt.QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout = QtW.QVBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.icon)
        self.setLayout(self.layout)
        self.icon.mousePressEvent = self.on_click

    def on_click(self, event):
        print(self.meter_id)

    def color(self, color: tuple):
        self.img = color_icon(self.img, color)
        qtimg = QImage(ImageQt.ImageQt(self.img))
        self.icon.setPixmap(QPixmap.fromImage(qtimg))

    def __repr__(self) -> str:
        return f"Meter({self.meter_id}, text={self.text.text()})"

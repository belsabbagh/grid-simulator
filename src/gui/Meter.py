from PyQt6 import QtWidgets as QtW
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image, ImageQt
import PyQt6 as Qt
from PyQt6 import QtCore


def color_icon(img: Image.Image, color: tuple) -> Image.Image:
    """Replace solid black pixels with a color"""
    img.putdata([color if px[-1] != 0 else px for px in img.getdata()]) # type: ignore
    return img


class Meter(QtW.QWidget):
    icon: QtW.QLabel
    meter_id: str
    text: QtW.QLabel

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
        self.text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout = QtW.QVBoxLayout() # type: ignore
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.icon)
        self.setLayout(self.layout)
        self.mousePressEvent = self.on_click # type: ignore
        self.setObjectName("meter")
        self.setStyleSheet("#meter {background-color: transparent; border: none;}")

    def on_click(self, event) -> None:
        print(self.meter_id)

    def color(self, color: tuple) -> None:
        self.img = color_icon(self.img, color)
        qtimg = QImage(ImageQt.ImageQt(self.img))
        self.icon.setPixmap(QPixmap.fromImage(qtimg))

    def __repr__(self) -> str:
        return f"Meter({self.meter_id}, text={self.text.text()})"

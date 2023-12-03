import math
from PyQt6 import QtWidgets as QtW
from PyQt6.QtGui import QPen, QColor
from src.gui.Meter import Meter


def circle_coords(n, r, offset=None):
    """Returns n points on a circle with radius r"""
    if offset is None:
        offset = (0, 0)
    fns = (math.cos, math.sin)
    for x in range(1, n + 1):
        yield (r * fn(2 * math.pi / n * x) + o for o, fn in zip(offset, fns))


def iter_all_pairs(lst):
    """Iterate over all pairs in a list"""
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if i != j:
                yield lst[i], lst[j]


class MetersGrid(QtW.QWidget):
    """MetersGrid Functionality:
    - `connect(m1, m2, color)` - connect two meters with a line of color
    - `connect_all(color)` - connect all meters with a line of color
    - `color_meter(meter_id, color)` - color a meter with a color
    - `set_text_meter(meter_id, text)` - set the text of a meter
    """
    meters: dict[str, Meter]
    canvas: QtW.QGraphicsView

    def __init__(self, meter_ids, meter_size) -> None:
        super().__init__()
        csize = 600
        self.meter_size = meter_size
        pos = (0, 0)
        offset = (pos[0] + csize / 2, pos[1] + csize / 2)
        r = csize / 2 - meter_size / 2
        self.scene = QtW.QGraphicsScene()
        self.canvas = QtW.QGraphicsView(self.scene)
        self.canvas.setScene(self.scene)
        self.meters = {k: Meter(k, meter_size) for k in meter_ids}
        for pos, mid in zip(circle_coords(len(meter_ids), r, offset), meter_ids):
            self.canvas.scene().addWidget(self.meters[mid])
            self.meters[mid].move(*[int(i) for i in pos])
        self.canvas.update()
        self.layout = QtW.QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

    def __get_meter_pos(self, meter_id):
        return self.meters[meter_id].pos()

    def __get_connection_pos(self, meter_id):
        pos = self.__get_meter_pos(meter_id)
        return (pos.x() + self.meter_size - 10, pos.y() + self.meter_size + 5)

    def connect(self, m1, m2, color):
        p1 = self.__get_connection_pos(m1)
        p2 = self.__get_connection_pos(m2)
        pen = QPen(QColor(*color))
        pen.setWidth(4)
        line = self.scene.addLine(*p1, *p2, pen)
        line.setZValue(-1)

    def connect_all(self, color):
        for m1, m2 in iter_all_pairs(list(self.meters.keys())):
            self.connect(m1, m2, color)

    def color_meter(self, meter_id, color):
        self.meters[meter_id].color(color)

    def set_text_meter(self, meter_id, text):
        self.meters[meter_id].text.setText(text)


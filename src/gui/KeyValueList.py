import PyQt6 as Qt
import PyQt6.QtWidgets as QtW
import time
class KeyValueList(QtW.QWidget):
    def __init__(self, data: dict) -> None:
        super().__init__()
        self.layout = QtW.QVBoxLayout() # type: ignore
        self.setLayout(self.layout)
        font = self.font()
        font.setPointSize(16)
        font.setBold(True)
        for key, value in data.items():
            kv_layout = QtW.QHBoxLayout()
            k_lavel, v_label = QtW.QLabel(f"{key}: "), QtW.QLabel(str(value))
            k_lavel.setFont(font)
            vfont = v_label.font()
            vfont.setPointSize(14)
            v_label.setFont(vfont)
            kv_layout.addWidget(k_lavel)
            kv_layout.addWidget(v_label)
            kv_layout.setSpacing(0)
            self.layout.addLayout(kv_layout)
            
    def update(self, data: dict) -> None:
        for i in range(self.layout.count()):
            layout = self.layout.itemAt(i)
            key = layout.itemAt(0).widget().text()[:-2]
            value = data[key]
            layout.itemAt(1).widget().setText(str(value))

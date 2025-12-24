import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QCheckBox, QPushButton, QApplication, QFrame
from PyQt6.QtGui import QPixmap, QGuiApplication, QIcon, QPalette
from PyQt6.QtCore import Qt

from app.views.image_label import ClickableImageLabel
from app.models.parking_info import ParkingInfo
from app.types import Status, text_for


class FilterWidget(QFrame):
    def __init__(self):
        super().__init__()

        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(2)

        layout = QVBoxLayout()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['None'] + [text_for(status) for status in Status])
        # self.filter_combo.currentIndexChanged.connect(self.update_index)
        layout.addWidget(self.filter_combo)

        self.filter_option_combo = QComboBox()
        self.filter_option_combo.addItems(['None', 'GT不明', '入庫見逃し', '出庫見逃し', '初回=True', '初回=False', 'PlateConf=NG', 'PlateConf=OK', 'TopFormat=NG', 'TopFormat=OK', 'BottomFormat=NG', 'BottomFormat=OK'])
        layout.addWidget(self.filter_option_combo)

        self.filter_index_label = QLabel()
        layout.addWidget(self.filter_index_label)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.raw_label = ClickableImageLabel(scale=10)
        layout.addWidget(self.raw_label)

        self.combo = QComboBox()
        self.combo.addItems([text_for(status) for status in Status])
        self.combo.setEnabled(False)
        # self.combo.currentIndexChanged.connect(self.on_combo_changed)
        layout.addWidget(self.combo)

        self.setLayout(layout)

    def set_info(self, infos: list[ParkingInfo], index: int, it_dir: str, raw_dir: str):
        info = infos[index]
        self.info = info
        self.info_label.setText('index')
        self.info_label.setText(f'Lot: {info.lot}\nIs_Occupied: {info.is_occupied}\nVehicle_Status: {info.vehicle_status}\ntop: {info.lpr_top}\nbottom: {info.lpr_bottom}')

        path = os.path.join(raw_dir, info.name() + '_raw.jpg')
        self.raw_label.set(path, info)

        self.combo.setCurrentIndex(info.status.value)

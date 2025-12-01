import os, sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QCheckBox, QPushButton, QApplication
from PyQt6.QtGui import QPixmap, QGuiApplication, QIcon, QPalette
from PyQt6.QtCore import Qt


from app.views.image_label import ClickableImageLabel
from app.models.parking_info import ParkingInfo
from app.types import Status, text_for
from app.utlis import parse_timestamp, format_jst, diff_timestamp

class FilterWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.info_label = QLabel()
        self.info_label.setText('index')
        layout.addWidget(self.info_label)

        self.raw_label = ClickableImageLabel(10)
        layout.addWidget(self.raw_label)

        self.combo = QComboBox()
        self.combo.addItems([text_for(status) for status in Status])
        self.combo.isEnabled = False
        # self.combo.currentIndexChanged.connect(self.on_combo_changed)
        layout.addWidget(self.combo)

        self.setLayout(layout)

    def set_info(self, infos: list[ParkingInfo], index: int, it_dir: str, raw_dir: str):
        info = infos[index]
        self.info = info
        self.info_label.setText('index')
        self.info_label.setText(f'<b>{index+1} / {len(infos)} (Lot: {info.lot})</b>')

        path = os.path.join(raw_dir, info.name() + '_raw.jpg')
        self.raw_label.set(path)

        self.combo.setCurrentIndex(info.status.value)

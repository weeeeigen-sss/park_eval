import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QCheckBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


from app.models.parking_info import ParkingInfo
from app.types import Status, text_for

class ParkWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.info: ParkingInfo = None

        layout = QVBoxLayout()

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.raw_label = QLabel()
        layout.addWidget(self.raw_label)

        mid_layout = QHBoxLayout()
        self.vehicle_label = QLabel()
        mid_layout.addWidget(self.vehicle_label)

        mid_right_layout = QVBoxLayout()
        self.plate_label = QLabel()
        mid_right_layout.addWidget(self.plate_label)

        self.json_label = QLabel()
        mid_right_layout.addWidget(self.json_label)
        mid_layout.addLayout(mid_right_layout)

        layout.addLayout(mid_layout)

        self.combo = QComboBox()
        self.combo.addItems([text_for(status) for status in Status])
        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        layout.addWidget(self.combo)

        self.gt_unknown = QCheckBox('GT不明')
        self.gt_unknown.stateChanged.connect(self.on_gt_unknown_changed)
        layout.addWidget(self.gt_unknown)

        self.miss_in = QCheckBox('入庫見逃し')
        self.miss_in.stateChanged.connect(self.on_miss_in_changed)
        layout.addWidget(self.miss_in)

        self.miss_out = QCheckBox('出庫見逃し')
        self.miss_out.stateChanged.connect(self.on_miss_out_changed)
        layout.addWidget(self.miss_out)


        # レイアウトをウィジェットにセット
        self.setLayout(layout)

    def on_combo_changed(self, index):
        if self.info is not None:
            self.info.set(Status(index))

    def on_gt_unknown_changed(self, check):
        if self.info is not None:
            self.info.set_gt_unknown(check == Qt.CheckState.Checked.value)

    def on_miss_in_changed(self, check):
        if self.info is not None:
            self.info.set_miss_in(check == Qt.CheckState.Checked.value)

    def on_miss_out_changed(self, check):
        if self.info is not None:
            self.info.set_miss_out(check == Qt.CheckState.Checked.value)

    def set_info(self, infos: list[ParkingInfo], index: int, it_dir: str, raw_dir: str):
        info = infos[index]
        self.info = info

        # Update image
        path = os.path.join(it_dir, info.name() + '_plate.bmp')
        if os.path.exists(path):
            plate_pixmap = QPixmap(path)
            p_scaled_pixmap = plate_pixmap.scaled(plate_pixmap.width(), plate_pixmap.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.plate_label.setPixmap(p_scaled_pixmap)
        else:
            self.plate_label.setPixmap(QPixmap())

        path = os.path.join(it_dir, info.name() + '_vehicle.jpg')
        if os.path.exists(path):
            vehicle_pixmap = QPixmap(path)
            v_scaled_pixmap = vehicle_pixmap.scaled(vehicle_pixmap.width() // 4, vehicle_pixmap.height() // 4, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.vehicle_label.setPixmap(v_scaled_pixmap)
        else:
            self.vehicle_label.setPixmap(QPixmap())
            
        path = os.path.join(raw_dir, info.name() + '_raw.jpg')
        if os.path.exists(path):
            raw_pixmap = QPixmap(path)  
            scaled_pixmap = raw_pixmap.scaled(raw_pixmap.width() // 5, raw_pixmap.height() // 5, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.raw_label.setPixmap(scaled_pixmap)
        else:
            self.raw_label.setPixmap(QPixmap())

        # Update text
        self.info_label.setText(f'<b>{index} / {len(infos) - 1} (Lot: {info.lot})</b><br><br>' + \
            f'{info.json_file}<br>' + \
            f'TimeStamp: {info.timestamp}')
        
        color = "red" if index > 0 and info.is_occupied != infos[index - 1].is_occupied else "white"
        text = f'<font color="{color}">Is_Occupied: {info.is_occupied}</font><br>'

        color = "red" if index > 0 and info.is_occlusion != infos[index - 1].is_occlusion else "white"
        text += f'<font color="{color}">Is_Occlusion: {info.is_occlusion}</font><br>'

        color = "red" if index > 0 and info.vehicle_status != infos[index - 1].vehicle_status else "white"
        text += f'<font color="{color}">Vehicle_Status: {info.vehicle_status}</font><br>'

        color = "red" if index > 0 and info.lpr_top != infos[index - 1].lpr_top else "white"
        text += f'<font color="{color}">lpr_top: {info.lpr_top}</font><br>'

        color = "red" if index > 0 and info.lpr_bottom != infos[index - 1].lpr_bottom else "white"
        text += f'<font color="{color}">lpr_bottom: {info.lpr_bottom}</font><br>'

        self.json_label.setText(text)

        # Update status
        self.gt_unknown.setChecked(info.is_gt_unknown)
        self.miss_in.setChecked(info.is_miss_in)
        self.miss_out.setChecked(info.is_miss_out)
        self.combo.setCurrentIndex(info.status.value)

    # def set_empty(self):
    #     empty = QPixmap()
    #     self.plate_label.setPixmap(empty)
    #     self.vehicle_label.setPixmap(empty)
    #     self.raw_label.setPixmap(empty)

    #     self.info_label.setText('')
    #     self.json_label.setText('')

    #     self.set_checked_wo_signal(self.gt_unknown, False)
    #     self.set_checked_wo_signal(self.miss_in, False)
    #     self.set_checked_wo_signal(self.miss_out, False)
    #     self.set_current_index_wo_signal(self.combo, 0)

    # def set_checked_wo_signal(self, cb: QCheckBox, checkd: bool):
    #     cb.blockSignals(True)
    #     cb.setChecked(checkd)
    #     cb.blockSignals(False)

    # def set_current_index_wo_signal(self, cb: QComboBox, index: int):
    #     cb.blockSignals(True)
    #     cb.setCurrentIndex(index)
    #     cb.blockSignals(False)
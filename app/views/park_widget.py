import os
import subprocess

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QCheckBox, QPushButton
from PyQt6.QtGui import QPixmap, QGuiApplication, QIcon
from PyQt6.QtCore import Qt


from app.views.image_label import ClickableImageLabel
from app.models.parking_info import ParkingInfo
from app.types import Status, text_for
from app.utlis import parse_timestamp, format_jst, diff_timestamp

class ParkWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.info: ParkingInfo = None

        layout = QVBoxLayout()

        # Info
        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        # Json
        json_row = QHBoxLayout()
        self.json_label = QLabel()
        json_row.addWidget(self.json_label)

        self.json_copy = QPushButton()
        self.json_copy.setIcon(QIcon.fromTheme("document-open"))
        self.json_copy.setFixedSize(24, 24)
        self.json_copy.setToolTip("Reveal in Finder")
        self.json_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.json_copy.clicked.connect(self.on_json_clicked)
        json_row.addWidget(self.json_copy)

        json_row.addStretch()
        layout.addLayout(json_row)

        # Timestamp
        timestamp_row = QHBoxLayout()
        self.timestamp_label = QLabel()
        timestamp_row.addWidget(self.timestamp_label)

        self.timestamp_copy = QPushButton()
        self.timestamp_copy.setIcon(QIcon.fromTheme("edit-copy"))
        self.timestamp_copy.setFixedSize(24, 24)
        self.timestamp_copy.setToolTip("Copy Timestamp")
        self.timestamp_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timestamp_copy.clicked.connect(self.on_time_clicked)
        timestamp_row.addWidget(self.timestamp_copy)

        timestamp_row.addStretch()
        layout.addLayout(timestamp_row)

        # JST
        jst_row = QHBoxLayout()
        self.jst_label = QLabel()
        jst_row.addWidget(self.jst_label)

        self.jst_copy = QPushButton()
        self.jst_copy.setIcon(QIcon.fromTheme("edit-copy"))
        self.jst_copy.setFixedSize(24, 24)
        self.jst_copy.setToolTip("Copy JST")
        self.jst_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.jst_copy.clicked.connect(self.on_jst_clicked)
        jst_row.addWidget(self.jst_copy)

        jst_row.addStretch()
        layout.addLayout(jst_row)

        # RAW Image
        self.raw_label = ClickableImageLabel(5)
        layout.addWidget(self.raw_label)

        # Plate Image
        self.plate_label = ClickableImageLabel()
        self.plate_label.setFixedSize(309, 159)
        self.plate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.plate_label)

        mid_layout = QHBoxLayout()

        # Vehicle Image
        self.vehicle_label = ClickableImageLabel(4)
        self.vehicle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mid_layout.addWidget(self.vehicle_label)        

        mid_right_layout = QVBoxLayout()

        # Param
        self.param_label = QLabel()
        mid_right_layout.addWidget(self.param_label)

        self.lp_button = QPushButton('Copy LP')
        self.lp_button.clicked.connect(self.on_lp_clicked)
        mid_right_layout.addWidget(self.lp_button)

        mid_layout.addLayout(mid_right_layout)

        layout.addLayout(mid_layout)

        # Status combo
        self.combo = QComboBox()
        self.combo.addItems([text_for(status) for status in Status])
        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        layout.addWidget(self.combo)

        # Option checkboxs
        option_layout = QHBoxLayout()

        self.gt_unknown = QCheckBox('GT不明')
        self.gt_unknown.stateChanged.connect(self.on_gt_unknown_changed)
        option_layout.addWidget(self.gt_unknown)

        self.miss_in = QCheckBox('入庫見逃し')
        self.miss_in.stateChanged.connect(self.on_miss_in_changed)
        option_layout.addWidget(self.miss_in)

        self.miss_out = QCheckBox('出庫見逃し')
        self.miss_out.stateChanged.connect(self.on_miss_out_changed)
        option_layout.addWidget(self.miss_out)

        layout.addLayout(option_layout)

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

    def on_json_clicked(self):
        if self.info is not None:
            if os.path.exists(self.info.json_path):
                # Finderで選択状態で開く（macOS専用）
                subprocess.run(["open", "-R", str(self.info.json_path)])

    def on_time_clicked(self):
        if self.info is not None:
            clipboard = QGuiApplication.clipboard()
            text = f'{self.info.timestamp}'
            clipboard.setText(text)

    def on_jst_clicked(self):
        if self.info is not None:
            clipboard = QGuiApplication.clipboard()
            text = f'{format_jst(parse_timestamp(self.info.timestamp))}'
            clipboard.setText(text)

    def on_lp_clicked(self):
        if self.info is not None:
            clipboard = QGuiApplication.clipboard()
            text = str(self.info.lpr_top) + '\n' + str(self.info.lpr_bottom)
            clipboard.setText(text)

    def set_info(self, infos: list[ParkingInfo], index: int, it_dir: str, raw_dir: str):
        info = infos[index]
        self.info = info

        # Update images
        path = os.path.join(it_dir, info.name() + '_plate.bmp')
        self.plate_label.set(path)

        path = os.path.join(it_dir, info.name() + '_vehicle.jpg')
        self.vehicle_label.set(path)

        path = os.path.join(raw_dir, info.name() + '_raw.jpg')
        self.raw_label.set(path)


        # Update info label
        self.info_label.setText(f'<b>{index+1} / {len(infos)} (Lot: {info.lot})</b>')
        self.json_label.setText(f'{info.json_file}')
        self.timestamp_label.setText(f'TimeStamp: {info.timestamp}')

        text = f'日本時間: {format_jst(parse_timestamp(info.timestamp))}'
        if index > 0:
            hours, minutes, seconds = diff_timestamp(infos[index - 1].timestamp, info.timestamp)
            if hours > 0:
                text += f'（+ {int(hours)}時間{int(minutes)}分{seconds:.0f}秒）'
            elif minutes > 0:
                text += f'（+ {int(minutes)}分{seconds:.0f}秒）'
            else:
                text += f'（+ {seconds:.0f}秒）'

        self.jst_label.setText(text)
        
        # Update json label
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

        text += f'<font color="white">Score: {self.info.plate_score}<br>Confidence: {self.info.plate_confidence}</font>'

        self.param_label.setText(text)

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
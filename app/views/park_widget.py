import os, sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QCheckBox, QPushButton, QApplication
from PyQt6.QtGui import QPixmap, QGuiApplication, QIcon, QPalette
from PyQt6.QtCore import Qt


from app.views.image_label import ClickableImageLabel
from app.views.json_widget import JsonWindow
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

        self.json_open = QPushButton()
        self.json_open.setIcon(QIcon.fromTheme("dialog-information"))
        self.json_open.setFixedSize(24, 24)
        self.json_open.setToolTip("Open JSON Viewer")
        self.json_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.json_open.clicked.connect(self.show_json)
        json_row.addWidget(self.json_open)

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
        self.raw_label = ClickableImageLabel(show_border=True, scale=5)
        layout.addWidget(self.raw_label)

        # Plate Image
        plate_layout = QHBoxLayout()
        self.plate_label = ClickableImageLabel()
        self.plate_label.setFixedSize(240, 100)
        self.plate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plate_layout.addWidget(self.plate_label)

        plate_info_layout = QVBoxLayout()
        self.plate_lp_label = QLabel('LPR Result')
        plate_info_layout.addWidget(self.plate_lp_label)

        self.lp_button = QPushButton('Copy LP')
        self.lp_button.clicked.connect(self.on_lp_clicked)
        plate_info_layout.addWidget(self.lp_button)
        plate_info_layout.addStretch()
        plate_layout.addLayout(plate_info_layout)
        plate_layout.addStretch()

        layout.addLayout(plate_layout)

        mid_layout = QHBoxLayout()

        # Vehicle Image
        self.vehicle_label = ClickableImageLabel(scale=4)
        self.vehicle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mid_layout.addWidget(self.vehicle_label)        

        mid_right_layout = QVBoxLayout()

        # Param
        self.param_label = QLabel()
        mid_right_layout.addWidget(self.param_label)

        

        mid_layout.addLayout(mid_right_layout)

        layout.addLayout(mid_layout)

        # Status combo
        self.combo = QComboBox()
        self.combo.addItems([text_for(status) for status in Status])
        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        layout.addWidget(self.combo)

        # Option checkboxs
        option_layout = QHBoxLayout()

        self.is_first = QCheckBox('初回')
        self.is_first.stateChanged.connect(self.on_first_park_changed)
        option_layout.addWidget(self.is_first)

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

        btn = QPushButton("Copy Widget Image")
        btn.clicked.connect(self.copy_me)
        layout.addWidget(btn)

        self.setLayout(layout)

    def copy_me(self):
        pix = QPixmap(self.size())
        pix.fill(Qt.GlobalColor.transparent)
        self.render(pix)

        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(pix)

    def on_combo_changed(self, index):
        if self.info is not None:
            self.info.set(Status(index))

            self.is_first.setEnabled(self.info.vehicle_status == 'Stop' or self.info.status == Status.Wrong_Out)


    def on_first_park_changed(self, check):
        if self.info is not None:
            self.info.set_first_park(check == Qt.CheckState.Checked.value)

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
                if sys.platform == "win32":
                    # Explorerで選択状態で開く（Windows専用）
                    subprocess.run(["explorer", "/select,", str(Path(self.info.json_path))])
                elif sys.platform == "darwin":
                    # Finderで選択状態で開く（macOS専用）
                    subprocess.run(["open", "-R", str(Path(self.info.json_path))])

    def show_json(self):
        if self.info is None:
            return
        # 新しいウィンドウを生成して表示
        self.json_window = JsonWindow(self.info.json_data)
        self.json_window.show()

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
        self.plate_label.set(path, info)

        path = os.path.join(it_dir, info.name() + '_vehicle.jpg')
        self.vehicle_label.set(path, info)

        path = os.path.join(raw_dir, info.name() + '_raw.jpg')
        self.raw_label.set(path, info)


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
        palette = QApplication.palette()
        normal_color = palette.color(QPalette.ColorRole.WindowText).name()

        color = "red" if index > 0 and info.is_occupied != infos[index - 1].is_occupied else normal_color
        text = f'<font color="{color}">Is_Occupied: {info.is_occupied}</font><br>'

        color = "red" if index > 0 and info.is_occlusion != infos[index - 1].is_occlusion else normal_color
        text += f'<font color="{color}">Is_Occlusion: {info.is_occlusion}</font><br>'

        color = "red" if index > 0 and info.vehicle_status != infos[index - 1].vehicle_status else normal_color
        text += f'<font color="{color}">Vehicle_Status: {info.vehicle_status}</font><br>'

        score_text = f'{float(info.plate_score):.3f}' if info.plate_score is not None else 'N/A'
        text += f'<font color="{normal_color}">Plate Score: {score_text}</font><br>'

        color = "yellow" if info.is_conf_ng() else normal_color
        conf_text = f'{float(info.plate_confidence):.3f}' if info.plate_confidence is not None else 'N/A'
        text += f'<font color="{color}">Plate Confidence: {conf_text}</font><br>'

        self.param_label.setText(text)

        plate_text = ''
        color = "red" if index > 0 and info.lpr_top != infos[index - 1].lpr_top else normal_color
        plate_text += f'<font color="{color}">{info.lpr_top if info.lpr_top is not None else "N/A"}</font>'
        color = "yellow" if info.is_top_format_ng() else normal_color
        plate_text += f'<font color="{color}"> ({"OK" if color != "yellow" else "NG"})</font><br>'

        color = "red" if index > 0 and info.lpr_bottom != infos[index - 1].lpr_bottom else normal_color
        plate_text += f'<font color="{color}">{info.lpr_bottom if info.lpr_bottom is not None else "N/A"}</font>'
        color = "yellow" if info.is_bottom_format_ng() else normal_color
        plate_text += f'<font color="{color}"> ({"OK" if color != "yellow" else "NG"})</font><br>'
        self.plate_lp_label.setText(plate_text)

        # Update status
        # self.combo.setEnabled(info.vehicle_status != 'Moving')
        self.is_first.setEnabled(info.vehicle_status == 'Stop' or info.status == Status.Wrong_Out)

        self.is_first.setChecked(info.is_first)
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
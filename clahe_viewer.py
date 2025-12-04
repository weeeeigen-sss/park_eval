import sys
import os
import csv

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QMainWindow, QToolBar, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QGuiApplication, QPalette


from app.controllers.data_manager import load
from app.models.parking_info import ParkingInfo
from app.types import Status, text_for

from enum import Enum


class ClaheInfo:
    def __init__(self, path: str, info: ParkingInfo):
        self.path = path
        self.info = info

        self.labels = dict[str, Status]()

        self.lprs = []
        lpr_csv = os.path.join(path, 'LPR_result.csv')
        if os.path.exists(lpr_csv):
            with open(lpr_csv, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # header = next(reader)
                for row in reader:
                    self.lprs.append(row)

        label_csv = os.path.join(path, 'label.csv')
        if os.path.exists(label_csv):
            with open(label_csv, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # header = next(reader)
                for row in reader:
                    status = Status(int(row['status']))
                    self.labels[row['image_name']] = status

        if 'original' not in self.labels:
            self.labels['original'] = info.status
        if '1x1' not in self.labels:
            self.labels['1x1'] = info.status
        if '4x2' not in self.labels:
            self.labels['4x2'] = info.status
        if '8x4' not in self.labels:
            self.labels['8x4'] = info.status

    @classmethod
    def create(cls, path: str, info: ParkingInfo):
        lpr_csv = os.path.join(path, 'LPR_result.csv')
        if os.path.exists(lpr_csv):
            if os.path.getsize(lpr_csv) == 0:
                print(f'Empty: {lpr_csv}')
                return None
        
        return ClaheInfo(path, info)
        


def load_clahe(path: str, infos: list[ParkingInfo]):
    result = []
    
    for dir in sorted(os.listdir(path)):
        if dir.startswith('.'):
            continue

        if not os.path.isdir(os.path.join(path, dir)):
            continue

        for d in sorted(os.listdir(os.path.join(path, dir))):
            if d.startswith('.'):
                continue
            split = os.path.splitext(d)[0].split('_')
            for info in infos:
                if info.name() == d:
                    clahe = ClaheInfo.create(os.path.join(path, dir, d), info)
                    if clahe is not None:
                        result.append(clahe)

    return result

class ClaheWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.image = QLabel()
        self.image.setMaximumSize(600, 600)
        layout.addWidget(self.image)

        self.param = QLabel()
        layout.addWidget(self.param)

        self.lpr_top = QLabel()
        self.lpr_top.setMaximumSize(600, 600)
        layout.addWidget(self.lpr_top)  

        self.lpr_bottom = QLabel()
        layout.addWidget(self.lpr_bottom)
        layout.addStretch()

        self.combo = QComboBox()
        self.combo.addItems([text_for(status) for status in Status])
        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        layout.addWidget(self.combo)

    def updateView(self, clahe: ClaheInfo, image_name: str):
        self.clahe = clahe
        self.image_name = image_name

        lpr = [lpr for lpr in clahe.lprs if lpr['image_name'] == image_name][0]
        # print(os.path.join(clahe.path, f'{image_name}.bmp'))
        pixmap = QPixmap(str(os.path.join(clahe.path, f'{image_name}.bmp')))

        # 指定した矩形領域を切り出し
        info = clahe.info
        rect = QRect(info.plate_xmin, info.plate_ymin, info.plate_width, info.plate_height)  # ← ここを任意の領域に変更
        cropped = pixmap.copy(rect)
        self.image.setPixmap(cropped)

        self.param.setText(image_name)

        palette = QApplication.palette()
        normal_color = palette.color(QPalette.ColorRole.WindowText).name()

        color = 'red' if  clahe.info.lpr_top != lpr['top_text'] else normal_color
        self.lpr_top.setText(f'<font color="{color}">{lpr["top_text"]}</font>')

        color = 'red' if  clahe.info.lpr_bottom != lpr['bottom_text'] else normal_color
        self.lpr_bottom.setText(f'<font color="{color}">{lpr["bottom_text"]}</font>')

        status = clahe.labels[image_name]
        self.combo.setCurrentIndex(status.value)

    def on_combo_changed(self, index):
        self.clahe.labels[self.image_name] = Status(index)
        

class MainWidget(QMainWindow):
    def __init__(self, info_path: str, clahe_path: str):
        super().__init__()

        self.info_path = info_path
        self.clahe_path = clahe_path

        merged_infos = []
        for dir in os.listdir(sys.argv[1]):
            if dir.startswith('.'):
                continue

            if dir == 'clahe_results':
                continue
            if not os.path.isdir(os.path.join(sys.argv[1], dir)):
                continue
            infos, lots = load(os.path.join(sys.argv[1], dir))
            print(f'Loaded {len(infos)} infos from {dir}')
            merged_infos.extend(infos)

        self.clahes: list[ClaheInfo] = load_clahe(clahe_path, merged_infos)
        print(f'Loaded {len(self.clahes)} clahe infos from {clahe_path}')


        self.filter_indices = None
        self.filter_index = 0
        self.filter_infos = self.clahes
        self.info_index = 0

        self.central = QWidget()
        layout = QHBoxLayout(self.central)

        info_layout = QVBoxLayout()

        self.plate_label = QLabel()
        self.plate_label.setMaximumSize(600, 600)
        info_layout.addWidget(self.plate_label)

        self.lpr_top_label = QLabel()
        info_layout.addWidget(self.lpr_top_label)

        self.lpr_bottom_label = QLabel()    
        info_layout.addWidget(self.lpr_bottom_label)

        self.raw_label = QLabel()
        info_layout.addWidget(self.raw_label)
        layout.addLayout(info_layout)

        self.info_label = QLabel()
        info_layout.addWidget(self.info_label)

        clahe_layout = QHBoxLayout(self.central)

        self.original = ClaheWidget()
        clahe_layout.addWidget(self.original)

        self.one_one = ClaheWidget()
        clahe_layout.addWidget(self.one_one)
        
        self.four_two = ClaheWidget()
        clahe_layout.addWidget(self.four_two)

        self.eight_four = ClaheWidget()
        clahe_layout.addWidget(self.eight_four)

        clahe_layout.addStretch()
        layout.addLayout(clahe_layout)

        self.setCentralWidget(self.central)

        # Toolbar
        toolbar = QToolBar("My Toolbar")
        toolbar.setMovable(False)   # 動かしたくない場合
        self.addToolBar(toolbar)

        self.index_label = QLabel()
        toolbar.addWidget(self.index_label)

        self.save_button = QPushButton('Save Labels')
        self.save_button.clicked.connect(self.save_labels)
        toolbar.addWidget(self.save_button)

        # Init
        self.update_views()
        self.configure_shortcuts()


    def save_labels(self):
        # Save labels
        for clahe in self.clahes:
            label_csv = os.path.join(clahe.path, 'label.csv')
            with open(label_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'image_name', 'status', 'status_text'])
                for image_name, status in clahe.labels.items():
                    writer.writerow([clahe.info.name(), image_name, status.value, status.name])

        # Save summary
        summary_csv = os.path.join(self.clahe_path, 'clahe_label_summary.csv')
        with open(summary_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['image_name', 'ok', 'ng_shadow', 'ng_others', 'ok_to_ng', 'ng_shadow_to_ok', 'ng_others_to_ok'])
            
            # Write original counts
            base_ok = [clahe for clahe in self.clahes if clahe.info.status == Status.OK]
            base_ng_shadow = [clahe for clahe in self.clahes if clahe.info.status == Status.NG_Shadow]
            base_ng_others = [clahe for clahe in self.clahes if clahe.info.status != Status.OK and clahe.info.status != Status.NG_Shadow]
            writer.writerow(['base', len(base_ok), len(base_ng_shadow), len(base_ng_others), '', '', ''])
            
            # Write clahe counts
            for image_name in ['original', '1x1', '4x2', '8x4']:
                ok = [clahe for clahe in self.clahes if clahe.labels.get(image_name) == Status.OK]
                ng_shadow = [clahe for clahe in self.clahes if clahe.labels.get(image_name) == Status.NG_Shadow]
                ng_others = [clahe for clahe in self.clahes if clahe.labels.get(image_name) != Status.OK and clahe.labels.get(image_name) != Status.NG_Shadow]
            
                ok_to_ng = [clahe for clahe in base_ok if clahe.labels.get(image_name) != Status.OK]
                ng_shadow_to_ok = [clahe for clahe in base_ng_shadow if clahe.labels.get(image_name) == Status.OK]
                ng_others_to_ok = [clahe for clahe in base_ng_others if clahe.labels.get(image_name) == Status.OK]

                writer.writerow([image_name, len(ok), len(ng_shadow), len(ng_others), len(ok_to_ng), len(ng_shadow_to_ok), len(ng_others_to_ok)])
        self.statusBar().showMessage('Labels saved')

    def update_views(self):
        clahe = self.filter_infos[self.info_index]

        self.index_label.setText(f'{self.info_index + 1} / {len(self.filter_infos)}')

        plate_pixmap = QPixmap((clahe.info.image_base() + '_plate.bmp'))
        print((clahe.info.image_base() + '_plate.bmp'))
        self.plate_label.setPixmap(plate_pixmap)

        self.lpr_top_label.setText(f'{clahe.info.lpr_top} ({clahe.info.top_quality})')
        self.lpr_bottom_label.setText(f'{clahe.info.lpr_bottom} ({clahe.info.bottom_quality})')

        self.info_label.setText(f'Timestamp: {clahe.info.timestamp}\nLot: {clahe.info.lot}\nStatus: {clahe.info.status.name}\nVehicle Status: {clahe.info.vehicle_status}')
        raw_pixmap = QPixmap(os.path.join(self.info_path, 'RAW', clahe.info.name() + '_raw.jpg'))
        self.raw_label.setPixmap(raw_pixmap.scaled(raw_pixmap.width() // 5, raw_pixmap.height() // 5, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.original.updateView(clahe, 'original')
        self.one_one.updateView(clahe, '1x1')
        self.four_two.updateView(clahe, '4x2')
        self.eight_four.updateView(clahe, '8x4')

    def configure_shortcuts(self):
        shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        shortcut.activated.connect(self.copy_screenshot)

    def copy_screenshot(self):
        # ウィンドウ全体をキャプチャ
        pixmap = self.grab()

        # クリップボードにコピー
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(pixmap)

    def keyPressEvent(self, event):
        if len(self.clahes) > 0:
            if event.key() == Qt.Key.Key_Left:
                if self.filter_indices != None:
                    flag = self.filter_index <= 0
                    self.filter_index = len(self.filter_indices) - 1 if flag else self.filter_index - 1
                    
                    self.info_index = self.filter_indices[self.filter_index]
                    self.update_views()
                else:
                    flag = self.info_index <= 0
                    self.info_index = len(self.filter_infos) - 1 if flag else self.info_index - 1
                    self.update_views()
                    if flag:
                        self.statusBar().showMessage('最後尾に移動しました')
            elif event.key() == Qt.Key.Key_Right:
                if self.filter_indices != None:
                    flag = self.filter_index >= len(self.filter_indices) - 1
                    self.filter_index = 0 if flag else self.filter_index + 1

                    self.info_index = self.filter_indices[self.filter_index]
                    self.update_views()
                else:
                    flag = self.info_index >= len(self.filter_infos) - 1
                    self.info_index = 0 if flag else self.info_index + 1
                    self.update_views()
                    if flag:
                        self.statusBar().showMessage('先頭に移動しました')
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet("QWidget { font-size: 24pt; }")

    
    window = MainWidget(sys.argv[1], os.path.join(sys.argv[1], 'clahe_results'))
    # if len(sys.argv) == 2:
    #     window.load(sys.argv[1])
    window.show()
    sys.exit(app.exec())
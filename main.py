import sys
import os
import json
import csv
from enum import Enum

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox, QMainWindow, QToolBar, QCheckBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class Status(Enum):
    NoLabel = 0
    OK = 1
    NG_Out = 2
    NG_Shadow = 3
    NG_Occlusion = 4
    NG_FP = 5
    NG_Blur = 6
    NG_Others = 7
    OK_Out = 8
    Wrong_Out = 9

def text_for(status: Status):
    if status == Status.NoLabel:
        return ''
    elif status == Status.OK:
        return 'OK'
    elif status == Status.NG_Out:
        return 'NG（見切れ）'
    elif status == Status.NG_Shadow:
        return 'NG（影）'
    elif status == Status.NG_Occlusion:
        return 'NG（Occlusion）'
    elif status == Status.NG_FP:
        return 'NG（FP）'
    elif status == Status.NG_Blur:
        return 'NG（ブラー）'
    elif status == Status.NG_Others:
        return 'NG（その他）'
    elif status == Status.OK_Out:
        return 'OK（出庫）'
    elif status == Status.Wrong_Out:
        return '誤出庫'

class ParkingInfo:
    def __init__(self, json_path):
        split = os.path.splitext(os.path.basename(json_path))[0].split('_')
        lot = split[1]
        self.is_ps = len(split) == 3

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            parking_lot_info = data["Inference_Results"][0]["parking_lot_info"]
            for info in parking_lot_info:
                if info["Lot"] != lot:
                    continue
                self.lot = info["Lot"]
                self.timestamp = str(info.get("TimeStamp"))
                self.json_file = os.path.basename(json_path)

                self.is_occupied = info.get("Is_Occupied")
                self.is_occlusion = info.get("Is_Occlusion")
                self.is_uncertain = info.get("Is_Uncertain")
                self.vehicle_status = info.get("Vehicle_Status")

                plate_number = info.get("Plate_Number", {})
                self.lpr_top = plate_number.get("Top")
                self.top_quality = plate_number.get("Top_Quality")
                self.lpr_bottom = plate_number.get("Bottom")
                self.bottom_quality = plate_number.get("Bottom_Quality")

                self.plate_confidence = info.get("Plate_Confidence")

                lpd_bbox = info.get("LPD_Bbox", {})
                self.plate_score = lpd_bbox.get("score")

                vehicle_bbox = info.get("Vehicle_Bbox", {})
                self.vehicle_score = vehicle_bbox.get("score")

                self.status = Status.NoLabel
                self.is_miss_in = False
                self.is_miss_out = False

    def name(self):
        name = self.timestamp + '_' + self.lot
        return name + '_ps' if self.is_ps else name
    
    def set(self, status: Status):
        self.status = status

    def create_row(self):
        return [f'{self.json_file}',f'{self.lot}', f'{self.is_occupied}', f'{int(self.is_miss_in)}',f'{int(self.is_miss_out)}',f'{self.status}']
    

class MainWidget(QMainWindow):
    def __init__(self, frames, path, infos: list[ParkingInfo], lots):
        super().__init__()

        self.frames = frames
        self.infos = infos
        self.filter_infos = infos
        self.lots = lots

        self.info_index = frames - 1

        self.path = path
        self.it_dir = os.path.join(path, 'IT')
        self.raw_dir = os.path.join(path, 'RAW')

        self.park_widgets: list[ParkWidget] = []

        central = QWidget()
        layout = QHBoxLayout(central)
        for i in range(0, self.frames):
            park_widget = ParkWidget()
            layout.addWidget(park_widget)
            self.park_widgets.append(park_widget)

        self.update_views()

        toolbar = QToolBar("My Toolbar")
        toolbar.setMovable(False)   # 動かしたくない場合
        self.addToolBar(toolbar)

        # ドロップダウン（コンボボックス）を作ってツールバーに追加
        self.lot_combo = QComboBox()
        self.lot_combo.addItems(['All'] + self.lots)
        self.lot_combo.currentIndexChanged.connect(self.on_lot_combo_changed)
        self.on_lot_combo_changed(0)
        toolbar.addWidget(self.lot_combo)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save)
        toolbar.addWidget(self.save_button)

        # self.setLayout(layout)
        self.setCentralWidget(central)
        self.setWindowTitle("park_eval")
    
    def on_lot_combo_changed(self, index):
        if index == 0:
            self.filter_infos = infos
            self.info_index = self.frames - 1
            self.update_views()
        else:
            self.filter_infos = [info for info in self.infos if info.lot == self.lots[index - 1]]
            self.info_index = self.frames - 1
            self.update_views()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.info_index = len(self.filter_infos) - 1 if self.info_index <= 0 else self.info_index - 1
            self.update_views()
        elif event.key() == Qt.Key.Key_Right:
            self.info_index = 0 if self.info_index >= len(self.filter_infos) - 1 else self.info_index + 1
            self.update_views()
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理

    def update_views(self):
        for i in range(0, self.frames):
            index = self.info_index - self.frames + 1 + i
            if 0 <= index < len(self.filter_infos):
                self.park_widgets[i].set_info(self.filter_infos, index, self.it_dir, self.raw_dir)
            else:
                self.park_widgets[i].set_empty()

    def save(self):
        path = os.path.join(self.path, 'label.csv')
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    'json',
                    'lot',
                    'is_occupied',
                    'is_miss_in',
                    'is_miss_out',
                    'status',
                    'status_label'
                    ])
            for info in self.infos:
                writer.writerow(
                    [
                        f'{info.json_file}',
                        f'{info.lot}', 
                        f'{info.is_occupied}', 
                        f'{int(info.is_miss_in)}',
                        f'{int(info.is_miss_out)}',
                        f'{info.status.value}',
                        f'{info.status}'
                        ])
        self.statusBar().showMessage(f'Save: {path}')


class ParkWidget(QWidget):
    def __init__(self):
        super().__init__()

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
        self.combo.currentIndexChanged.connect(
            lambda index: self.info.set(Status(index))
        )
        layout.addWidget(self.combo)

        self.miss_in = QCheckBox('入庫見逃し')
        layout.addWidget(self.miss_in)

        self.miss_out = QCheckBox('出庫見逃し')
        layout.addWidget(self.miss_out)


        # レイアウトをウィジェットにセット
        self.setLayout(layout)

    def set_info(self, infos: list[ParkingInfo], index: int, it_dir: str, raw_dir: str):
        info = infos[index]
        self.info = info

        # Update image
        path = os.path.join(it_dir, info.name() + '_plate.bmp')
        if os.path.exists(path):
            plate_pixmap = QPixmap(path)
            p_scaled_pixmap = plate_pixmap.scaled(plate_pixmap.width() // 2, plate_pixmap.height() // 2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.plate_label.setPixmap(p_scaled_pixmap)
        else:
            self.plate_label.setPixmap(QPixmap())

        path = os.path.join(it_dir, info.name() + '_vehicle.jpg')
        if os.path.exists(path):
            vehicle_pixmap = QPixmap(path)
            v_scaled_pixmap = vehicle_pixmap.scaled(vehicle_pixmap.width() // 2, vehicle_pixmap.height() // 2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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
        self.miss_in.setChecked(info.is_miss_in)
        self.miss_out.setChecked(info.is_miss_out)
        self.combo.setCurrentIndex(info.status.value)

    def set_empty(self):
        empty = QPixmap()
        self.plate_label.setPixmap(empty)
        self.vehicle_label.setPixmap(empty)
        self.raw_label.setPixmap(empty)

        self.info_label.setText('')
        self.json_label.setText('')

        self.miss_in.setChecked(False)
        self.miss_out.setChecked(False)
        self.combo.setCurrentIndex(0)

        
def load(path: str):
    meta_dir = os.path.join(path, 'META')
    json_files = [f for f in os.listdir(meta_dir) if f.endswith(".json")]
    json_files.sort()

    infos: list[ParkingInfo] = []
    lots = []
    for json_file in json_files:
        info = ParkingInfo(os.path.join(meta_dir, json_file))
        infos.append(info)
        if not info.lot in lots:
            lots.append(info.lot)

    return infos, lots       
    

if __name__ == "__main__":
    path = 'sample_data/20250910'
    infos, lots = load(path)

    label_csv = os.path.join(path, 'label.csv')
    with open(label_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # header = next(reader)
        for row in reader:
            match = [info for info in infos if info.json_file == row['json']]
            if len(match) == 1:
                match[0].is_miss_in = bool(int(row['is_miss_in']))
                match[0].is_miss_in = bool(int(row['is_miss_out']))
                match[0].status = Status(int(row['status']))
            else:
                print(row['json'])

    app = QApplication(sys.argv)
    window = MainWidget(3, path, infos, lots)
    window.show()
    sys.exit(app.exec())
import sys
import os
import json

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox, QMainWindow, QToolBar
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ParkingInfo:
    def __init__(self, json_path):
        lot = os.path.splitext(os.path.basename(json_path))[0].split('_')[1]

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

    def name(self):
        return self.timestamp + '_' + self.lot
    

class MainWidget(QMainWindow):
    def __init__(self, frames, path, infos: list[ParkingInfo], lots):
        super().__init__()

        self.frames = frames
        self.infos = infos
        self.filter_infos = infos
        self.lots = lots

        self.info_index = frames - 1
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



class ParkWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

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
        self.combo.addItems(['', 'OK', 'OK (2+)', 'NG（見切れ）', 'NG（影）', 'NG（オクルージョン）', '出庫見逃し', '入庫見逃し', '誤出庫'])

        layout.addWidget(self.combo)

        # レイアウトをウィジェットにセット
        self.setLayout(layout)

    def set_info(self, infos: list[ParkingInfo], index: int, it_dir: str, raw_dir: str):
        info = infos[index]

        path = os.path.join(it_dir, info.timestamp + '_' + info.lot + '_plate.bmp')
        if os.path.exists(path):
            plate_pixmap = QPixmap(path)
            p_scaled_pixmap = plate_pixmap.scaled(plate_pixmap.width() // 2, plate_pixmap.height() // 2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.plate_label.setPixmap(p_scaled_pixmap)
        else:
            self.plate_label.setPixmap(QPixmap())

        path = os.path.join(it_dir, info.timestamp + '_' + info.lot + '_vehicle.jpg')
        if os.path.exists(path):
            vehicle_pixmap = QPixmap(path)
            v_scaled_pixmap = vehicle_pixmap.scaled(vehicle_pixmap.width() // 4, vehicle_pixmap.height() // 4, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.vehicle_label.setPixmap(v_scaled_pixmap)
        else:
            self.vehicle_label.setPixmap(QPixmap())
            

        path = os.path.join(raw_dir, info.name() + '_raw.jpg')
        if os.path.exists(path):
            raw_pixmap = QPixmap(path)  
            scaled_pixmap = raw_pixmap.scaled(raw_pixmap.width() // 6, raw_pixmap.height() // 6, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.raw_label.setPixmap(scaled_pixmap)
        else:
            self.raw_label.setPixmap(QPixmap())

        text = f'<b>{index} / {len(infos) - 1}</b><br>' + \
            f'Json: {info.json_file}<br>' + \
            f'Lot: {info.lot}<br>' + \
            f'TimeStamp: {info.timestamp}<br>'

        
        color = "red" if index > 0 and info.is_occupied != infos[index - 1].is_occupied else "white"
        text += f'<font color="{color}">Is_Occupied: {info.is_occupied}</font><br>'

        color = "red" if index > 0 and info.is_occlusion != infos[index - 1].is_occlusion else "white"
        text += f'<font color="{color}">Is_Occlusion: {info.is_occlusion}</font><br>'

        color = "red" if index > 0 and info.vehicle_status != infos[index - 1].vehicle_status else "white"
        text += f'<font color="{color}">Vehicle_Status: {info.vehicle_status}</font><br>'

        color = "red" if index > 0 and info.lpr_top != infos[index - 1].lpr_top else "white"
        text += f'<font color="{color}">lpr_top: {info.lpr_top}</font><br>'

        color = "red" if index > 0 and info.lpr_bottom != infos[index - 1].lpr_bottom else "white"
        text += f'<font color="{color}">lpr_bottom: {info.lpr_bottom}</font><br>'

        self.json_label.setText(text)



        # text = f'<b>{index} / {len(infos) - 1}</b><br>' + \
        #     f'<b>Json: {self.json_file}</b><br>' + \
        #     f'<b>Lot: {self.lot}</b><br>' + \
        #     f'<b>TimeStamp: {self.timestamp}</b><br>' + \
        #     f'Is_Occupied: {self.is_occupied}<br>' + \
        #     f'Is_Occlusion: {self.is_occlusion}<br>' + \
        #     f'Vehicle_Status: {self.vehicle_status}<br>' + \
        #     f'lpr_top: {self.lpr_top}<br>' + \
        #     f'lpr_bottom: {self.lpr_bottom}'


    def set_empty(self):
        empty = QPixmap()
        self.plate_label.setPixmap(empty)
        self.vehicle_label.setPixmap(empty)
        self.raw_label.setPixmap(empty)

        self.json_label.setText('')


    # def update_view(self):
    #     pixmap1 = QPixmap(os.path.join(self.it_dir, infos[self.info_index].timestamp + '_' + infos[self.info_index].lot + '_plate.bmp'))  # 画像ファイルのパス
    #     self.plate_label.setPixmap(pixmap1)

    #     pixmap2 = QPixmap(os.path.join(self.it_dir, infos[self.info_index].timestamp + '_' + infos[self.info_index].lot + '_vehicle.jpg'))
    #     self.vehicle_label.setPixmap(pixmap2)

        


def load(path: str):
    meta_dir = os.path.join(path, 'META')
    json_files = [f for f in os.listdir(meta_dir) if f.endswith(".json")]
    json_files.sort()

    infos = []
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
    
    app = QApplication(sys.argv)
    window = MainWidget(3, path, infos, lots)
    window.show()
    sys.exit(app.exec())
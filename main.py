import sys
import os
import json

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class MyWidget(QWidget):
    def __init__(self, path, infos):
        super().__init__()

        # レイアウト作成（縦に並べる）
        layout = QHBoxLayout()

        self.infos = infos
        self.info_index = 0
        self.it_dir = os.path.join(path, 'IT')
        self.raw_dir = os.path.join(path, 'RAW')

        self.raw_label = QLabel()
        pixmap = QPixmap(os.path.join(self.raw_dir, infos[self.info_index].name() + '_raw.jpg'))
        scaled_pixmap = pixmap.scaled(pixmap.width() // 4, pixmap.height() // 4, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.raw_label.setPixmap(scaled_pixmap)
        layout.addWidget(self.raw_label)

        left_layout = QVBoxLayout()

        self.vehicle_label = QLabel()
        pixmap2 = QPixmap(os.path.join(self.it_dir, infos[self.info_index].name() + '_vehicle.jpg'))
        self.vehicle_label.setPixmap(pixmap2)
        left_layout.addWidget(self.vehicle_label)

        # self.raw_label = QLabel()
        # pixmap = QPixmap(os.path.join(self.raw_dir, infos[self.info_index].name() + '_raw.jpg'))
        # scaled_pixmap = pixmap.scaled(pixmap.width() // 4, pixmap.height() // 4, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        # self.raw_label.setPixmap(scaled_pixmap)
        # left_layout.addWidget(self.raw_label)

        layout.addLayout(left_layout)

        center_layout = QVBoxLayout()

        self.plate_label = QLabel()
        pixmap1 = QPixmap(os.path.join(it_dir, infos[self.info_index].name() + '_plate.bmp'))  # 画像ファイルのパス
        self.plate_label.setPixmap(pixmap1)
        center_layout.addWidget(self.plate_label)

        # テキスト
        self.text_label = QLabel(infos[self.info_index].text())
        center_layout.addWidget(self.text_label)
        center_layout.addStretch() 

        layout.addLayout(center_layout)

        right_layout = QVBoxLayout()
        # ボタンなどの操作
        self.button = QPushButton("OK")        
        right_layout.addWidget(self.button)

        self.button2 = QPushButton("NG")
        right_layout.addWidget(self.button2)

        layout.addLayout(right_layout)


        # レイアウトをウィジェットにセット
        self.setLayout(layout)
        self.setWindowTitle("画像・テキスト・操作UI")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.info_index = len(self.infos) - 1 if self.info_index <= 0 else self.info_index - 1
            self.update_view()
        elif event.key() == Qt.Key.Key_Right:
            self.info_index = 0 if self.info_index >= len(self.infos) - 1 else self.info_index + 1
            self.update_view()
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理

    def update_view(self):
        pixmap1 = QPixmap(os.path.join(self.it_dir, infos[self.info_index].timestamp + '_' + infos[self.info_index].lot + '_plate.bmp'))  # 画像ファイルのパス
        self.plate_label.setPixmap(pixmap1)

        pixmap2 = QPixmap(os.path.join(self.it_dir, infos[self.info_index].timestamp + '_' + infos[self.info_index].lot + '_vehicle.jpg'))
        self.vehicle_label.setPixmap(pixmap2)

        

class ParkingInfo:
    def __init__(self, json_path):
        lot = os.path.splitext(json_path)[0].split('_')[1]

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            parking_lot_info = data["Inference_Results"][0]["parking_lot_info"]
            for info in parking_lot_info:
                if info["Lot"] != lot:
                    continue
                self.lot = info["Lot"]
                self.timestamp = str(info.get("TimeStamp"))

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
    
    def text(self):
        return f'Is_Occupied: {self.is_occupied}\nIs_Occlusion: {self.is_occlusion}\nVehicle_Status: {self.vehicle_status}\nPlate_Number: {self.lpr_top} + {self.lpr_bottom}'


def load(path: str):
    meta_dir = os.path.join(path, 'META')
    json_files = [f for f in os.listdir(meta_dir) if f.endswith(".json")]
    json_files.sort()

    infos = []
    for json_file in json_files:
        info = ParkingInfo(os.path.join(meta_dir, json_file))
        infos.append(info)

    return infos        
    

if __name__ == "__main__":
    path = '/Users/Yusaku.Eigen/Desktop/20250910'
    infos = load(path)
    it_dir = os.path.join('/Users/Yusaku.Eigen/Desktop/20250910', 'IT')
    
    app = QApplication(sys.argv)
    window = MyWidget(path, infos)
    window.show()
    sys.exit(app.exec())
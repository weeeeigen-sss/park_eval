import os, sys, csv
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox, QMainWindow, QToolBar, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QGuiApplication, QKeyEvent

from PyQt6.QtWidgets import QApplication
           
from app.controllers.data_manager import load
from app.views.image_label import ClickableImageLabel
from app.types import Status, text_for
from app.models.parking_info import ParkingInfo

class EBSIMWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.raw_label = ClickableImageLabel(show_plate_rect=True, show_vehicle_rect=True, scale=5)
        layout.addWidget(self.raw_label)

        plate_layout = QHBoxLayout()

        self.plate_label = ClickableImageLabel()
        plate_layout.addWidget(self.plate_label)

        self.plate_text_label = QLabel()
        plate_layout.addWidget(self.plate_text_label)

        layout.addLayout(plate_layout)

        self.is_first = QCheckBox('初回')
        self.is_first.stateChanged.connect(self.on_first_park_changed)
        self.is_first.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # フォーカスポリシーを設定
        layout.addWidget(self.is_first)

        wrong_layout = QHBoxLayout()

        self.wrong_top_checkbox = QCheckBox("Wrong Top")
        self.wrong_top_checkbox.setChecked(False)
        self.wrong_top_checkbox.stateChanged.connect(self.wrong_top_checkbox_changed)
        self.wrong_top_checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # フォーカスポリシーを設定
        wrong_layout.addWidget(self.wrong_top_checkbox)

        self.wrong_bottom_checkbox = QCheckBox("Wrong Bottom")
        self.wrong_bottom_checkbox.setChecked(False)
        self.wrong_bottom_checkbox.stateChanged.connect(self.wrong_bottom_checkbox_changed)
        self.wrong_bottom_checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # フォーカスポリシーを設定
        wrong_layout.addWidget(self.wrong_bottom_checkbox)    
        layout.addLayout(wrong_layout)

        self.combo = QComboBox()
        self.combo.addItems([text_for(status) for status in Status])
        self.combo.currentIndexChanged.connect(self.on_combo_changed)
        self.combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # フォーカスポリシーを設定
        layout.addWidget(self.combo)

        container = QWidget()
        container.setLayout(layout)
        container.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # フォーカスポリシーを設定
        self.setCentralWidget(container)

        # Toolbar
        toolbar = QToolBar("My Toolbar")
        toolbar.setMovable(False)   # 動かしたくない場合
        self.addToolBar(toolbar)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save)
        self.save_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # フォーカスポリシーを設定
        toolbar.addWidget(self.save_button)

    def load(self, path: str):
        # load
        infos, _ = load(path)
        if not infos:
            print("No data founded.")
            return
        
        self.path = path
        self.infos = infos
        self.wrong_top_infos = []
        self.wrong_bottom_infos = []
        self.index = 0
        
        # Load ebsim label csv
        ebsim_label_csv = os.path.join(path, 'ebsim_label.csv')
        if os.path.exists(ebsim_label_csv):
            with open(ebsim_label_csv, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # header = next(reader)
                for row in reader:
                    match = [info for info in infos if info.json_file == row['json']]
                    if len(match) == 1:
                        if 'top_correct' in row:
                            if row['top_correct'] == '0':
                                self.wrong_top_infos.append(match[0])

                        if 'bottom_correct' in row:
                            if row['bottom_correct'] == '0':
                                self.wrong_bottom_infos.append(match[0])
                            
                        if 'is_first' in row:
                            match[0].is_first = bool(int(row['is_first']))

                        if 'status' in row:
                            match[0].status = Status(int(row['status']))
                    else:
                        print(row['json'])
        
        
        self.update_view()

    def wrong_top_checkbox_changed(self, check):
        if check == Qt.CheckState.Checked.value:
            if self.infos[self.index] not in self.wrong_top_infos:
                self.wrong_top_infos.append(self.infos[self.index])
        else:
            if self.infos[self.index] in self.wrong_top_infos:
                self.wrong_top_infos.remove(self.infos[self.index])

        self.update_combo()

    def wrong_bottom_checkbox_changed(self, check):
        if check == Qt.CheckState.Checked.value:
            if self.infos[self.index] not in self.wrong_bottom_infos:
                self.wrong_bottom_infos.append(self.infos[self.index])
        else:
            if self.infos[self.index] in self.wrong_bottom_infos:
                self.wrong_bottom_infos.remove(self.infos[self.index])

        self.update_combo()


    def on_combo_changed(self, index):
        if self.infos is not None:
            self.infos[self.index].set(Status(index))

    def on_first_park_changed(self, check):
        if self.infos is not None:
            self.infos[self.index].set_is_first(check == Qt.CheckState.Checked.value)

    def keyPressEvent(self, event: QKeyEvent):
        if len(self.infos) > 0:
            if event.key() == Qt.Key.Key_Left:
                event.ignore()
                flag = self.index <= 0
                self.index = len(self.infos) - 1 if flag else self.index - 1
                self.update_view()
                if flag:
                    self.statusBar().showMessage('最後尾に移動しました')
                    
            elif event.key() == Qt.Key.Key_Right:
                event.ignore()
                flag = self.index >= len(self.infos) - 1
                self.index = 0 if flag else self.index + 1
                self.update_view()
                if flag:
                    self.statusBar().showMessage('先頭に移動しました')

            elif event.key() == Qt.Key.Key_F:
                if len(self.infos) > 0:
                    current_info = self.infos[self.index]
                    is_first = current_info.is_first
                    current_info.set_is_first(not is_first)

                    self.update_view()

            elif event.key() == Qt.Key.Key_T:
                if len(self.infos) > 0:
                    current_info = self.infos[self.index]
                    if self.infos[self.index] not in self.wrong_top_infos:
                        self.wrong_top_infos.append(self.infos[self.index])
                    else:
                        self.wrong_top_infos.remove(self.infos[self.index])

                    self.update_view()

            elif event.key() == Qt.Key.Key_B:
                if len(self.infos) > 0:
                    current_info = self.infos[self.index]
                    if self.infos[self.index] not in self.wrong_bottom_infos:
                        self.wrong_bottom_infos.append(self.infos[self.index])
                    else:
                        self.wrong_bottom_infos.remove(self.infos[self.index])

                    self.update_view()
                    
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理
        
    def update_view(self):
        info = self.infos[self.index]

        self.plate_text_label.setText(f'{info.lpr_top} ({float(info.top_quality):.3f})\n{info.lpr_bottom} ({float(info.bottom_quality):.3f})\n')

        image_path = os.path.join(self.path, 'isp', info.timestamp + '.png')
        self.raw_label.set(image_path, info)

        self.plate_label.set(image_path, info, rect=QRect(info.plate_xmin, info.plate_ymin, info.plate_xmax - info.plate_xmin, info.plate_ymax - info.plate_ymin))

        self.is_first.setChecked(info.is_first)

        if info in self.wrong_top_infos:
            self.wrong_top_checkbox.setChecked(True)
        else:
            self.wrong_top_checkbox.setChecked(False)

        if info in self.wrong_bottom_infos:
            self.wrong_bottom_checkbox.setChecked(True)
        else:
            self.wrong_bottom_checkbox.setChecked(False)

        self.update_combo()

    def update_combo(self):
        if self.wrong_top_checkbox.isChecked() or self.wrong_bottom_checkbox.isChecked():
            self.combo.setEnabled(True)
            self.combo.setCurrentIndex(self.infos[self.index].status.value)
        else:
            self.combo.setEnabled(False)

    def save(self):
        if not self.path:
            return
        save_path = self.save_label()
        self.statusBar().showMessage(f'Saved: {save_path}')

    def save_label(self):
        path = os.path.join(self.path, 'ebsim_label.csv')
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    'json',
                    'Timestamp',
                    'lot',

                    'vehicle_xmin', 'vehicle_ymin',
                    'vehicle_xmax', 'vehicle_ymax',
                    'vehicle_wdith', 'vehicle_height',
                    'vehicle_score',

                    'lpr_top', 'top_quality',
                    'lpr_bottom', 'bottom_quality',

                    'plate_xmin', 'plate_ymin',
                    'plate_xmax', 'plate_ymax',
                    'plate_width', 'plate_height',
                    'plate_score',
                    'plate_confidence',
                    'plate_count',

                    'car_num',
                    'top_correct', 'bottom_correct',
                    'top_correct_quality', 'top_incorrect_quality', 
                    'bottom_correct_quality', 'bottom_incorrect_quality',

                    'is_first',
                    'status',
                    'status_label'
                    ])
            
            car_num = 0
            for info in self.infos:
                if info.is_first:
                    car_num += 1
                writer.writerow(
                    [
                        f'{info.json_file}',
                        f'{info.timestamp}',
                        f'{info.lot}', 


                        f'{info.vehicle_xmin}', f'{info.vehicle_ymin}',
                        f'{info.vehicle_xmax}', f'{info.vehicle_ymax}',
                        f'{info.vehicle_wdith}', f'{info.vehicle_height}',
                        f'{info.vehicle_score}',

                        f'{info.lpr_top}', f'{info.top_quality}',
                        f'{info.lpr_bottom}', f'{info.bottom_quality}',

                        f'{info.plate_xmin}', f'{info.plate_ymin}',
                        f'{info.plate_xmax}', f'{info.plate_ymax}',
                        f'{info.plate_width}', f'{info.plate_height}',
                        f'{info.plate_score}',

                        f'{info.plate_confidence}',

                        f'{info.plate_count}',

                        f'{car_num}',
                        '0' if info in self.wrong_top_infos else '1', '0' if info in self.wrong_bottom_infos else '1', 
                        '' if info in self.wrong_top_infos else info.top_quality, info.top_quality if info in self.wrong_top_infos else '', 
                        '' if info in self.wrong_bottom_infos else info.bottom_quality,info.bottom_quality if info in self.wrong_bottom_infos else '',
                        
                        f'{int(info.is_first)}',
                        f'{info.status.value}',
                        f'{info.status}'
                    ])
        return path


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = EBSIMWidget()
    if len(sys.argv) == 2:
        window.load(sys.argv[1])
    window.show()
    sys.exit(app.exec())
import os, sys

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox, QMainWindow, QToolBar, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QGuiApplication

from PyQt6.QtWidgets import QApplication
           
from app.controllers.data_manager import load
from app.views.image_label import ClickableImageLabel

class EBSIMWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.raw_label = ClickableImageLabel(show_plate_rect=True, show_vehicle_rect=True, scale=5)
        layout.addWidget(self.raw_label)

        self.plate_label = ClickableImageLabel()
        layout.addWidget(self.plate_label)

        self.plate_text_label = QLabel()
        layout.addWidget(self.plate_text_label)

        self.is_first = QCheckBox('初回')
        self.is_first.stateChanged.connect(self.on_first_park_changed)
        layout.addWidget(self.is_first)

        self.wrong_checkbox = QCheckBox("Wrong")
        self.wrong_checkbox.setChecked(False)
        self.wrong_checkbox.stateChanged.connect(self.wrong_checkbox_changed)
        layout.addWidget(self.wrong_checkbox)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load(self, path: str):
        # load
        infos, lots = load(path)
        if not infos:
            print("No data founded.")
            return
        
        self.path = path
        self.infos = infos
        self.wrong_infos = []
        self.index = 0
        self.update_view()

    def wrong_checkbox_changed(self, check):
        if check == Qt.CheckState.Checked.value:
            if self.infos[self.index] not in self.wrong_infos:
                self.wrong_infos.append(self.infos[self.index])
        else:
            if self.infos[self.index] in self.wrong_infos:
                self.wrong_infos.remove(self.infos[self.index])

    def on_first_park_changed(self, check):
        if self.infos is not None:
            self.infos[self.index].set_is_first(check == Qt.CheckState.Checked.value)

    def keyPressEvent(self, event):
        if len(self.infos) > 0:
            if event.key() == Qt.Key.Key_Left:
                flag = self.index <= 0
                self.index = len(self.infos) - 1 if flag else self.index - 1
                self.update_view()
                if flag:
                    self.statusBar().showMessage('最後尾に移動しました')
                    
            elif event.key() == Qt.Key.Key_Right:
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
                    
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理
        
    def update_view(self):
        info = self.infos[self.index]

        self.plate_text_label.setText(f'{info.lpr_top}\n{info.lpr_bottom}')

        image_path = os.path.join(self.path, 'isp', info.timestamp + '.png')
        self.raw_label.set(image_path, info)

        self.plate_label.set(image_path, info, rect=QRect(info.plate_xmin, info.plate_ymin, info.plate_xmax - info.plate_xmin, info.plate_ymax - info.plate_ymin))

        self.is_first.setChecked(info.is_first)

        if info in self.wrong_infos:
            self.wrong_checkbox.setChecked(True)
        else:
            self.wrong_checkbox.setChecked(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = EBSIMWidget()
    if len(sys.argv) == 2:
        window.load(sys.argv[1])
    window.show()
    sys.exit(app.exec())
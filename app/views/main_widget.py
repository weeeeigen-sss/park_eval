import os

from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QComboBox, QMainWindow, QToolBar, QFileDialog, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QGuiApplication


from app.types import Status, text_for
from app.models.parking_info import ParkingInfo
from app.views.park_widget import ParkWidget
from app.controllers.data_manager import load, save_label, save_eval

class MainWidget(QMainWindow):
    def __init__(self, frames):
        super().__init__()

        self.frames = frames
        self.path = None
        self.infos: list[ParkingInfo] = []

        self.park_widgets: list[ParkWidget] = []

        central = QWidget()
        layout = QHBoxLayout(central)
        for i in range(0, self.frames):
            park_widget = ParkWidget()
            layout.addWidget(park_widget)
            self.park_widgets.append(park_widget)

        toolbar = QToolBar("My Toolbar")
        toolbar.setMovable(False)   # 動かしたくない場合
        self.addToolBar(toolbar)

        self.load_button = QPushButton('Load')
        self.load_button.clicked.connect(self.load)
        toolbar.addWidget(self.load_button)

        # ドロップダウン（コンボボックス）を作ってツールバーに追加
        self.lot_combo = QComboBox()
        self.lot_combo.currentIndexChanged.connect(self.on_lot_combo_changed)
        toolbar.addWidget(self.lot_combo)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_label)
        toolbar.addWidget(self.save_button)

        self.eval_button = QPushButton('Eval')
        self.eval_button.clicked.connect(self.save_eval)
        toolbar.addWidget(self.eval_button)

        self.filter_combo = QComboBox()
        self.filter_combo.currentIndexChanged.connect(self.on_status_combo_changed)
        self.filter_combo.addItems(['None', 'GT不明', '入庫見逃し', '出庫見逃し'] + [text_for(status) for status in Status])
        toolbar.addWidget(self.filter_combo)

        self.filter_index_label = QLabel()
        toolbar.addWidget(self.filter_index_label)

        # self.setLayout(layout)
        self.setCentralWidget(central)
        self.setWindowTitle("park_eval")

        # Shortcuts
        self.configure_shortcuts()

    def load(self):
        path = QFileDialog.getExistingDirectory(None, "フォルダを選択")
        if not path:
            print("No data selected.")
            return

        infos, lots = load(path)
        
        # Configure
        self.infos = infos
        self.filter_infos = infos
        self.lots = lots
        self.info_index = self.frames - 1

        self.filter_indices: list[int] = None
        self.filter_index = 0
        self.filter_combo.setCurrentIndex(0)

        self.path = path
        self.it_dir = os.path.join(path, 'IT')
        self.raw_dir = os.path.join(path, 'RAW')

        self.lot_combo.clear()
        self.lot_combo.addItems(['All'] + self.lots)
        self.on_lot_combo_changed(0)

        self.update_views()

        self.statusBar().showMessage(f'Load: {path}')


    
    def on_lot_combo_changed(self, index):
        if index == 0:
            self.filter_infos = self.infos
            self.info_index = self.frames - 1
            self.update_views()
        else:
            self.filter_infos = [info for info in self.infos if info.lot == self.lots[index - 1]]
            self.info_index = self.frames - 1
            self.update_views()
            # if self.filter_indices == None:
            #     self.info_index = self.frames - 1
            #     self.update_views()
            # else:
            #     self.on_status_combo_changed(self.filter_combo.currentIndex())


    def on_status_combo_changed(self, index):
        if index == 0:
            self.filter_indices = None
        else:
            if index == 1:
                self.filter_indices = [i for i, info in enumerate(self.infos) if info.is_gt_unknown == True]
            elif index == 2:
                self.filter_indices = [i for i, info in enumerate(self.infos) if info.is_miss_in == True]
            elif index == 3:
                self.filter_indices = [i for i, info in enumerate(self.infos) if info.is_miss_out == True]
            else:
                self.filter_indices = [i for i, info in enumerate(self.infos) if info.status == Status(index - 4)]

            if len(self.filter_indices) == 0:
                self.filter_combo.setCurrentIndex(0)
                return

            self.filter_index = 0
            self.info_index = self.filter_indices[self.filter_index]

            self.update_views()


    def keyPressEvent(self, event):
        if len(self.infos) > 0:
            if event.key() == Qt.Key.Key_Left:
                if self.filter_indices != None:
                    flag = self.filter_index <= 0
                    self.filter_index = len(self.filter_indices) - 1 if flag else self.filter_index - 1
                    
                    self.info_index = self.filter_indices[self.filter_index]
                    self.update_views()
                else:
                    flag = self.info_index <= self.frames - 1
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
                    self.info_index = self.frames - 1 if flag else self.info_index + 1
                    self.update_views()
                    if flag:
                        self.statusBar().showMessage('先頭に移動しました')
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理

    def update_views(self):
        if self.filter_indices != None:
            self.filter_index_label.setText(f'({self.filter_index + 1} / {len(self.filter_indices)})')
        else:
            self.filter_index_label.setText('')

        for i in range(0, self.frames):
            index = self.info_index - self.frames + 1 + i
            if 0 <= index < len(self.filter_infos):
                self.park_widgets[i].set_info(self.filter_infos, index, self.it_dir, self.raw_dir)
            # else:
                # self.park_widgets[i].set_empty()
                # print('Wrong Index:' + str(index))

    def save_label(self):
        if not self.path:
            return
        
        path = save_label(self.path, self.infos)
        self.statusBar().showMessage(f'Saved label: {path}')

    def save_eval(self):
        if not self.path:
            return
        
        path = save_eval(self.path, self.lots, self.infos)
        self.statusBar().showMessage(f'Saved eval: {path}')

    def configure_shortcuts(self):
        shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        shortcut.activated.connect(self.copy_screenshot)

    def copy_screenshot(self):
        # ウィンドウ全体をキャプチャ
        pixmap = self.grab()

        # クリップボードにコピー
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(pixmap)

         
        
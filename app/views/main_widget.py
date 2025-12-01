import os

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox, QMainWindow, QToolBar, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QGuiApplication


from app.types import Status, text_for
from app.models.parking_info import ParkingInfo
from app.views.park_widget import ParkWidget
from app.views.filter_widget import FilterWidget
from app.controllers.data_manager import load, eval, save_label, save_eval

class MainWidget(QMainWindow):
    def __init__(self, frames):
        super().__init__()

        self.frames = frames
        self.path = None
        self.infos: list[ParkingInfo] = []

        self.park_widgets: list[ParkWidget] = []
        self.filter_widgets: list[FilterWidget] = []

        self.tabs = QTabWidget()
        
        # Label tab
        label_view = QWidget()
        layout = QHBoxLayout(label_view)

        filter_layout = QVBoxLayout()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['None', 'GT不明', '入庫見逃し', '出庫見逃し', 'PlateConf NG', 'Format NG'] + [text_for(status) for status in Status])
        self.filter_combo.currentIndexChanged.connect(self.update_index)
        filter_layout.addWidget(self.filter_combo)

        self.filter_index_label = QLabel()
        filter_layout.addWidget(self.filter_index_label)

        for i in range(0, 5):
            filter_widget = FilterWidget()
            filter_layout.addWidget(filter_widget)
            self.filter_widgets.append(filter_widget)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        for i in range(0, self.frames):
            park_widget = ParkWidget()
            layout.addWidget(park_widget)
            self.park_widgets.append(park_widget)
        self.tabs.addTab(label_view, 'labeling')

        # Eval tab
        self.eval_view = QTableWidget(17, 2)
        self.tabs.addTab(self.eval_view, 'eval')
        self.tabs.currentChanged.connect(self.on_tabbar_clicked)

        # Toolbar
        toolbar = QToolBar("My Toolbar")
        toolbar.setMovable(False)   # 動かしたくない場合
        self.addToolBar(toolbar)

        self.load_button = QPushButton('Load')
        self.load_button.clicked.connect(self.load)
        toolbar.addWidget(self.load_button)

        # ドロップダウン（コンボボックス）を作ってツールバーに追加
        self.lot_combo = QComboBox()
        self.lot_combo.currentIndexChanged.connect(self.update_index)
        toolbar.addWidget(self.lot_combo)

        self.show_moving = QCheckBox('Show Moving')
        self.show_moving.setChecked(True)
        self.show_moving.stateChanged.connect(self.update_index)
        toolbar.addWidget(self.show_moving)

        

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_label)
        toolbar.addWidget(self.save_button)

        self.eval_button = QPushButton('Eval')
        self.eval_button.clicked.connect(self.save_eval)
        toolbar.addWidget(self.eval_button)

        # self.setLayout(layout)
        self.setCentralWidget(self.tabs)
        self.setWindowTitle("park_eval")

        # Shortcuts
        self.configure_shortcuts()

    def load(self, path:str = None):
        if not path:
            path = QFileDialog.getExistingDirectory(None, "フォルダを選択")
        
        if not path:
            print("No data selected.")
            return
        
        if not os.path.exists(path):
            print("Not exitst")
            return

        infos, lots = load(path)
        if not infos:
            print("No data founded.")
            return
        
        # Configure
        self.infos = infos
        self.current_infos = infos
        self.lots = lots
        self.info_index = self.frames - 1

        self.filter_infos: list[ParkingInfo] = []
        self.filter_index = 0
        self.filter_combo.setCurrentIndex(0)

        self.path = path
        self.it_dir = os.path.join(path, 'IT')
        self.raw_dir = os.path.join(path, 'RAW')

        self.lot_combo.clear()
        self.lot_combo.addItems(['All'] + self.lots)
        # self.on_lot_combo_changed(0)

        self.update_index()
        # self.update_views()

        self.statusBar().showMessage(f'Load: {path}')

    def update_index(self):
        lot_index = self.lot_combo.currentIndex()
        show_moving = self.show_moving.isChecked()
        filter_index = self.filter_combo.currentIndex()

        current_infos = self.infos if show_moving else [info for info in self.infos if info.vehicle_status != 'Moving']

        # Filter by lot
        if lot_index == 0:
            self.current_infos = current_infos
        else:
            self.current_infos = [info for info in current_infos if info.lot == self.lots[lot_index - 1]]

        # Filter by status
        if filter_index == 0:
            self.filter_infos = []
            self.info_index = self.frames - 1
        else:
            if filter_index == 1:
                self.filter_infos = [info for info in self.current_infos if info.is_gt_unknown == True]
            elif filter_index == 2:
                self.filter_infos = [info for info in self.current_infos if info.is_miss_in == True]
            elif filter_index == 3:
                self.filter_infos = [info for info in self.current_infos if info.is_miss_out == True]
            elif filter_index == 4:
                self.filter_infos = [info for info in self.current_infos if info.is_conf_ng()]
            elif filter_index == 5:
                self.filter_infos = [info for info in self.current_infos if info.is_format_ng()]
            else:
                self.filter_infos = [info for info in self.current_infos if info.status == Status(filter_index - 6)]

            if len(self.filter_infos) == 0:
                self.filter_combo.setCurrentIndex(0)
                return

            self.filter_index = 0
            self.info_index = self.current_infos.index(self.filter_infos[self.filter_index])

        self.update_views()


    def keyPressEvent(self, event):
        if len(self.infos) > 0:
            if event.key() == Qt.Key.Key_Left:
                flag = self.info_index <= self.frames - 1
                self.info_index = len(self.current_infos) - 1 if flag else self.info_index - 1
                self.update_views()
                if flag:
                    self.statusBar().showMessage('最後尾に移動しました')
                    
            elif event.key() == Qt.Key.Key_Right:
                flag = self.info_index >= len(self.current_infos) - 1
                self.info_index = self.frames - 1 if flag else self.info_index + 1
                self.update_views()
                if flag:
                    self.statusBar().showMessage('先頭に移動しました')
                    
            elif event.key() == Qt.Key.Key_Up:
                if self.filter_infos != None:
                    flag = self.filter_index <= 0
                    self.filter_index = len(self.filter_infos) - 1 if flag else self.filter_index - 1

                    self.info_index = self.current_infos.index(self.filter_infos[self.filter_index])
                    self.update_views()

            elif event.key() == Qt.Key.Key_Down:
                if self.filter_infos != None:
                    flag = self.filter_index >= len(self.filter_infos) - 1
                    self.filter_index = 0 if flag else self.filter_index + 1

                    self.info_index = self.current_infos.index(self.filter_infos[self.filter_index])
                    self.update_views()
                    
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理

    def update_views(self):
        if self.filter_infos != None:
            self.filter_index_label.setText(f'({self.filter_index + 1} / {len(self.filter_infos)})')
        else:
            self.filter_index_label.setText('')

        for i in range(0, len(self.filter_widgets)):
            index = self.filter_index + i
            if index < len(self.filter_infos):
                self.filter_widgets[i].set_info(self.filter_infos, index, self.it_dir, self.raw_dir)

        for i in range(0, self.frames):
            index = self.info_index - self.frames + 1 + i
            if 0 <= index < len(self.current_infos):
                self.park_widgets[i].set_info(self.current_infos, index, self.it_dir, self.raw_dir)
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
        
        path, eval_results = save_eval(self.path, self.lots, self.infos)
        self.statusBar().showMessage(f'Saved eval: {path}')

        self.update_eval_table(eval_results)

    def update_eval_table(self, eval_results=None):
        if eval_results == None:
            eval_results = eval(self.lots, self.infos)

        for i, (k,v) in enumerate(eval_results.items()):
            self.eval_view.setItem(i, 0, QTableWidgetItem(k))
            item = QTableWidgetItem(str(v))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.eval_view.setItem(i, 1, item)
        self.eval_view.resizeColumnsToContents()

    def on_tabbar_clicked(self, index):
        if index == 1:
            self.update_eval_table()

    def configure_shortcuts(self):
        shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        shortcut.activated.connect(self.copy_screenshot)

        shortcut_left = QShortcut(QKeySequence("Ctrl+Shift+["), self)
        shortcut_left.activated.connect(self.prev_tab)

        shortcut_right = QShortcut(QKeySequence("Ctrl+Shift+]"), self)
        shortcut_right.activated.connect(self.next_tab)

    def prev_tab(self):
        i = self.tabs.currentIndex()
        self.tabs.setCurrentIndex((i - 1) % self.tabs.count())

    def next_tab(self):
        i = self.tabs.currentIndex()
        self.tabs.setCurrentIndex((i + 1) % self.tabs.count())

    def copy_screenshot(self):
        # ウィンドウ全体をキャプチャ
        pixmap = self.grab()

        # クリップボードにコピー
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(pixmap)

         
        
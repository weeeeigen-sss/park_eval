import os

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox, QMainWindow, QToolBar, QFileDialog, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QGuiApplication


from app.types import Status, text_for, key_status_map
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

        self.json_window = None

        self.tabs = QTabWidget()
        
        # Label tab
        label_view = QWidget()
        layout = QHBoxLayout(label_view)

        side_layout = QVBoxLayout()

        # self.filter_combo = QComboBox()
        # self.filter_combo.addItems(['None', 'GT不明', '入庫見逃し', '出庫見逃し', '初回', 'PlateConf=NG', 'TopFormat=NG', 'BottomFormat=NG'] + [text_for(status) for status in Status])
        # self.filter_combo.currentIndexChanged.connect(self.update_index)
        # side_layout.addWidget(self.filter_combo)

        # self.filter_index_label = QLabel()
        # side_layout.addWidget(self.filter_index_label)

        # for i in range(0, 4):
        self.filter_widget = FilterWidget()
        self.filter_widget.filter_combo.currentIndexChanged.connect(self.update_index)
        self.filter_widget.filter_option_combo.currentIndexChanged.connect(self.update_index)
        side_layout.addWidget(self.filter_widget)
        # self.filter_widgets.append(filter_widget)

        side_layout.addStretch()

        label_help = QLabel()
        for k, v in key_status_map.items():
            label_help.setText(label_help.text() + f'[{k.name.replace("Key_", "")}]: {text_for(v)} \n')
        side_layout.addWidget(label_help)
        layout.addLayout(side_layout)

        for i in range(0, self.frames):
            park_widget = ParkWidget()
            layout.addWidget(park_widget)
            self.park_widgets.append(park_widget)
        self.tabs.addTab(label_view, 'labeling')

        # Eval tab
        self.eval_view = QTableWidget(19, 3)
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

        self.show_moving = QCheckBox('Moving')
        self.show_moving.setChecked(True)
        self.show_moving.stateChanged.connect(self.update_index)
        toolbar.addWidget(self.show_moving)

        self.show_stop = QCheckBox('Stop')
        self.show_stop.setChecked(True)
        self.show_stop.stateChanged.connect(self.update_index)
        toolbar.addWidget(self.show_stop)

        self.show_none = QCheckBox('None')
        self.show_none.setChecked(True)
        self.show_none.stateChanged.connect(self.update_index)
        toolbar.addWidget(self.show_none)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save)
        toolbar.addWidget(self.save_button)

        self.auto_label_button = QPushButton('AutoLabel Moving')
        self.auto_label_button.clicked.connect(self.auto_label_moving)
        toolbar.addWidget(self.auto_label_button)

        self.show_border = QCheckBox('Show Border')
        self.show_border.setChecked(True)
        self.show_border.stateChanged.connect(self.on_show_border_changed)
        toolbar.addWidget(self.show_border)

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
        self.filter_widget.filter_combo.setCurrentIndex(0)
        self.filter_widget.filter_option_combo.setCurrentIndex(0)

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
        show_stop = self.show_stop.isChecked()
        show_none = self.show_none.isChecked()
        filter_status_index = self.filter_widget.filter_combo.currentIndex()
        filter_option_index = self.filter_widget.filter_option_combo.currentIndex()


        current_infos = self.infos if show_moving else [info for info in self.infos if info.vehicle_status != 'Moving']
        current_infos = current_infos if show_stop else [info for info in current_infos if info.vehicle_status != 'Stop']
        current_infos = current_infos if show_none else [info for info in current_infos if info.vehicle_status != None]

        # Filter by lot
        if lot_index == 0:
            self.current_infos = current_infos
        else:
            self.current_infos = [info for info in current_infos if info.lot == self.lots[lot_index - 1]]

        # For reset filter
        if filter_status_index == 0 and filter_option_index == 0:
            self.filter_infos = []
            self.info_index = self.frames - 1
        else:
            # Filter by status
            self.filter_infos = [info for info in self.current_infos if info.status == Status(filter_status_index - 1)]

            # For no infos, reset filter
            if len(self.filter_infos) == 0:
                self.filter_widget.filter_combo.setCurrentIndex(0)
                self.filter_widget.filter_option_combo.setCurrentIndex(0)
                return
        
            # Filter by option
            if filter_option_index == 1:
                self.filter_infos = [info for info in self.filter_infos if info.is_gt_unknown == True]
            elif filter_option_index == 2:
                self.filter_infos = [info for info in self.filter_infos if info.is_miss_in == True]
            elif filter_option_index == 3:
                self.filter_infos = [info for info in self.filter_infos if info.is_miss_out == True]
            elif filter_option_index == 4:
                self.filter_infos = [info for info in self.filter_infos if info.is_first == True]
            elif filter_option_index == 5:
                self.filter_infos = [info for info in self.filter_infos if info.is_first == False]
            elif filter_option_index == 6:
                self.filter_infos = [info for info in self.filter_infos if info.is_conf_ng()]
            elif filter_option_index == 7:
                self.filter_infos = [info for info in self.filter_infos if not info.is_conf_ng()]
            elif filter_option_index == 8:
                self.filter_infos = [info for info in self.filter_infos if info.is_top_format_ng()]
            elif filter_option_index == 9:
                self.filter_infos = [info for info in self.filter_infos if not info.is_top_format_ng()]  
            elif filter_option_index == 10:
                self.filter_infos = [info for info in self.filter_infos if info.is_bottom_format_ng()]
            elif filter_option_index == 11:
                self.filter_infos = [info for info in self.filter_infos if not info.is_bottom_format_ng()]
            
            # For no infos, reset filter
            if len(self.filter_infos) == 0:
                self.filter_widget.filter_option_combo.setCurrentIndex(0)
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
                if len(self.filter_infos) > 0:
                    flag = self.filter_index <= 0
                    self.filter_index = len(self.filter_infos) - 1 if flag else self.filter_index - 1

                    self.info_index = self.current_infos.index(self.filter_infos[self.filter_index])
                    self.update_views()

            elif event.key() == Qt.Key.Key_Down:
                if len(self.filter_infos) > 0:
                    flag = self.filter_index >= len(self.filter_infos) - 1
                    self.filter_index = 0 if flag else self.filter_index + 1

                    self.info_index = self.current_infos.index(self.filter_infos[self.filter_index])
                    self.update_views()

            elif event.key() in key_status_map.keys():
                if len(self.filter_infos) > 0:
                    selected_status = key_status_map[event.key()]

                    info = self.current_infos[self.info_index]
                    info.set(selected_status)

                    self.update_views()
                    
        else:
            super().keyPressEvent(event)  # 他のキーはデフォルト処理

    def update_views(self):
        if len(self.filter_infos) > 0:
            self.filter_widget.filter_index_label.setText(f'({self.filter_index + 1} / {len(self.filter_infos)})')
            self.filter_widget.set_info(self.filter_infos, self.filter_index, self.it_dir, self.raw_dir)
        else:
            self.filter_widget.filter_index_label.setText('')

        # for i in range(0, len(self.filter_widgets)):
        #     index = self.filter_index + i
        #     if index < len(self.filter_infos):

        for i in range(0, self.frames):
            index = self.info_index - self.frames + 1 + i
            if 0 <= index < len(self.current_infos):
                self.park_widgets[i].set_info(self.current_infos, index, self.it_dir, self.raw_dir)
            # else:
                # self.park_widgets[i].set_empty()
                # print('Wrong Index:' + str(index))

    def save(self):
        if not self.path:
            return
        
        label_path = save_label(self.path, self.infos)
        
        path, eval_results = save_eval(self.path, self.lots, self.infos)
        self.statusBar().showMessage(f'Saved label: {label_path}, Saved eval: {path}')

        self.update_eval_table(eval_results)

    def auto_label_moving(self):
        for lot in self.lots:
            last = None

            for info in [self_info for self_info in self.infos if self_info.lot == lot]:
                if info.vehicle_status == 'Moving':
                    if last is not None:
                        if last.is_occupied == False:
                            info.set(Status.MovingIn)
                        elif last.is_occupied == True and last.vehicle_status == 'Stop':
                            info.set(Status.MovingOut)
                        elif last.is_occupied == True and last.vehicle_status == 'Moving':
                            info.set(last.status)
                    else:
                        if info.is_occupied == False:
                            info.set(Status.MovingIn)
                        else:
                            info.set(Status.MovingOut)
                last = info
        
        self.update_views()

    def eval_movement(self, threshold_y=0):
        for lot in self.lots:
            for info in [self_info for self_info in self.infos if self_info.lot == lot]:
                if info.vehicle_status == 'Stop':
                    # 誤出庫の場合、その後のStopは1回無視
                    if wrong_out_happened:
                        wrong_out_happened = False
                    else:
                        last_stop = info
                    continue

                if info.status == Status.Wrong_Out:
                    wrong_out_happened = True
                    continue
                
                if info.status == Status.MovingOut:
                    if last_stop is not None:
                        if info.move_plate_end_y is not None and info.move_plate_end_y < threshold_y:
                            info.set_stop_info(last_stop)
                            continue


    def update_eval_table(self, eval_results=None):
        if eval_results == None:
            eval_results = eval(self.lots, self.infos)

        for i, (k, (all_val, first_val)) in enumerate(eval_results.items()):
            self.eval_view.setItem(i, 0, QTableWidgetItem(k))
            
            item_all = QTableWidgetItem(str(all_val))
            item_all.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.eval_view.setItem(i, 1, item_all)
            
            item_first = QTableWidgetItem(str(first_val))
            item_first.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.eval_view.setItem(i, 2, item_first)
            
        self.eval_view.resizeColumnsToContents()

    def on_show_border_changed(self, state):
        for park_widget in self.park_widgets:
            park_widget.raw_label.setBorderVisible(state == Qt.CheckState.Checked.value)
        self.update_views()

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

         
        
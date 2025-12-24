import sys, os
import subprocess
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtGui import QPixmap, QCursor, QPixmap, QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QRect
from pathlib import Path

from app.models.parking_info import ParkingInfo

class ClickableImageLabel(QLabel):
    def __init__(self, show_status_rect: bool = False, show_plate_rect: bool = False, show_vehicle_rect: bool = False, scale:int=1):
        super().__init__()

        self.scale = scale
        self.image_path = None
        self.show_status_rect = show_status_rect
        self.show_plate_rect = show_plate_rect
        self.show_vehicle_rect = show_vehicle_rect
        self.info: ParkingInfo = None
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))  # 手のアイコンに変更

    def set(self, image_path: str, info: ParkingInfo):
        self.info = info
        if os.path.exists(image_path):
            self.image_path = Path(image_path)
            pixmap = QPixmap(str(self.image_path))
            scaled_pixmap = pixmap.scaled(pixmap.width() // self.scale, pixmap.height() // self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            self.setToolTip("Reveal in Finder")
        else:
            self.clear()
            self.setText('No Image')
            
    def mousePressEvent(self, event):
        if self.image_path is None:
            return
        if event.button() == Qt.MouseButton.LeftButton and self.image_path.exists():
            if sys.platform == "win32":
                # Explorerで選択状態で開く（Windows専用）
                subprocess.run(["explorer", "/select,", str(self.image_path)])
            elif sys.platform == "darwin":  
                # Finderで選択状態で開く（macOS専用）
                subprocess.run(["open", "-R", str(self.image_path)])
        super().mousePressEvent(event)

    def set_status_visible(self, visible: bool):
        self.show_status_rect = visible
        self.update()

    def set_plate_visible(self, visible: bool):
        self.show_plate_rect = visible
        self.update()

    def set_vehicle_visible(self, visible: bool):
        self.show_vehicle_rect = visible
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)    

        if self.info is None:
            return

        if self.show_status_rect:
            # Paint for vehicle status
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            w = self.width()
            h = self.height()

            rect = QRect(0, 0, w // 2, h) if self.info.lot == '00' else QRect(w // 2, 0, w - w // 2, h)
            if self.info.vehicle_status == 'Stop':
                pen = QPen(QColor(0, 255, 0, 255), 3)
                pen.setStyle(Qt.PenStyle.SolidLine)
            elif self.info.vehicle_status == 'Moving':
                pen = QPen(QColor(255, 255, 0, 255), 2)
                pen.setStyle(Qt.PenStyle.DotLine)
            else:
                pen = QPen(QColor(255, 255, 255, 255), 1)
                pen.setStyle(Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawRect(rect)

        # Paint plate bbox rect
        if self.show_plate_rect:
            if self.info.plate_xmin is not None and self.info.plate_ymin is not None and self.info.plate_xmax is not None and self.info.plate_ymax is not None:
                # 画像の表示サイズに合わせて座標をスケーリング
                # w_ratio = self.width() / (self.pixmap().width())
                # h_ratio = self.height() / (self.pixmap().height())

                plate_rect = QRect(
                    int(self.info.plate_xmin / self.scale),
                    int(self.info.plate_ymin / self.scale),
                    int((self.info.plate_xmax - self.info.plate_xmin) / self.scale),
                    int((self.info.plate_ymax - self.info.plate_ymin) / self.scale)
                )

                pen = QPen(QColor(0, 0, 255, 255), 2)
                pen.setStyle(Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawRect(plate_rect)

        # Paint vehicle bbox rect
        if self.show_vehicle_rect:
            if self.info.vehicle_xmax is not None and self.info.vehicle_ymax is not None and self.info.vehicle_xmin is not None and self.info.vehicle_ymin is not None:
                vehicle_rect = QRect(
                    int(self.info.vehicle_xmin / self.scale),
                    int(self.info.vehicle_ymin / self.scale),
                    int((self.info.vehicle_xmax - self.info.vehicle_xmin) / self.scale),
                    int((self.info.vehicle_ymax - self.info.vehicle_ymin) / self.scale)
                )

                pen = QPen(QColor(255, 0, 0, 255), 2)
                pen.setStyle(Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawRect(vehicle_rect)
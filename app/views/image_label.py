import sys, os
import subprocess
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt
from pathlib import Path


class ClickableImageLabel(QLabel):
    def __init__(self, scale:int=1):
        super().__init__()

        self.scale = scale

        # self.image_path = Path(image_path)

        # # 画像をセット
        # pixmap = QPixmap(str(self.image_path))
        # self.setPixmap(pixmap)
        # self.setScaledContents(True)  # QLabelサイズにスケール
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))  # 手のアイコンに変更

    def set(self, image_path: str):
        if os.path.exists(image_path):
            self.image_path = Path(image_path)
            pixmap = QPixmap(str(self.image_path))
            scaled_pixmap = pixmap.scaled(pixmap.width() // self.scale, pixmap.height() // self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
        else:
            self.clear()
            self.setText('No Image')
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.image_path.exists():
            # Finderで選択状態で開く（macOS専用）
            subprocess.run(["open", "-R", str(self.image_path)])
        super().mousePressEvent(event)
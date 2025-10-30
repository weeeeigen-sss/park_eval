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
        self.image_path = None
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))  # 手のアイコンに変更

    def set(self, image_path: str):
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
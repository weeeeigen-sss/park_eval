import sys

from PyQt6.QtWidgets import QApplication

from app.views.main_widget import MainWidget
           

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet("QWidget { font-size: 20pt; }")

    window = MainWidget(3)
    window.show()
    sys.exit(app.exec())
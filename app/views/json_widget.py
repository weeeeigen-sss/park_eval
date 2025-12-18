import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit
)


class JsonWindow(QWidget):
    def __init__(self, json_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JSON Viewer")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)

        # JSONを整形して表示
        pretty_json = json.dumps(json_data, indent=4, ensure_ascii=False)
        text_edit.setText(pretty_json)

        layout.addWidget(text_edit)
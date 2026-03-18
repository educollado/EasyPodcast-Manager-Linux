from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest


class ImagePreviewField(QWidget):
    """QLineEdit con miniatura de previsualización al lado."""

    SIZE = 64

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.editingFinished.connect(self._load_image)
        layout.addWidget(self.line_edit)

        self.preview = QLabel()
        self.preview.setFixedSize(self.SIZE, self.SIZE)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet(
            "border: 1px solid #e5dfd4; border-radius: 5px; background: #fff;"
        )
        self.preview.setText("·")
        layout.addWidget(self.preview)

    # --- API pública compatible con QLineEdit ---

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text or "")
        if text:
            self._load_image()

    def setPlaceholderText(self, text):
        self.line_edit.setPlaceholderText(text)

    # --- Carga de imagen ---

    def _load_image(self):
        url = self.line_edit.text().strip()
        if not url:
            self.preview.setText("·")
            self.preview.setPixmap(QPixmap())
            return
        request = QNetworkRequest(QUrl(url))
        reply = self._manager.get(request)
        reply.finished.connect(lambda: self._on_reply(reply))

    def _on_reply(self, reply):
        if reply.error() == reply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self.preview.setPixmap(
                    pixmap.scaled(
                        self.SIZE, self.SIZE,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self.preview.setText("?")
        reply.deleteLater()

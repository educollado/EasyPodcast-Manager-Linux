from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QScrollArea, QMessageBox
)
from api import APIError


SOCIAL_FIELDS = [
    ("blog", "Blog"),
    ("linkedin", "LinkedIn"),
    ("mastodon", "Mastodon"),
    ("x", "X (Twitter)"),
    ("instagram", "Instagram"),
    ("youtube", "YouTube"),
    ("github", "GitHub"),
    ("bluesky", "Bluesky"),
    ("pixelfed", "Pixelfed"),
]


class SocialTab(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._fields = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        from PySide6.QtWidgets import QWidget as W
        container = W()
        form = QFormLayout(container)
        scroll.setWidget(container)
        outer.addWidget(scroll)

        for key, label in SOCIAL_FIELDS:
            edit = QLineEdit()
            edit.setPlaceholderText(f"URL de {label}")
            self._fields[key] = edit
            form.addRow(f"{label}:", edit)

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_save = QPushButton("Guardar cambios")
        self.btn_save.clicked.connect(self._on_save)
        btn_bar.addWidget(self.btn_refresh)
        btn_bar.addWidget(self.btn_save)
        outer.addLayout(btn_bar)

    def refresh(self):
        try:
            data = self.api.get_social()
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las redes sociales:\n{e}")
            return
        for key, edit in self._fields.items():
            edit.setText(data.get(key, "") or "")

    def _on_save(self):
        data = {key: edit.text().strip() for key, edit in self._fields.items()}
        try:
            self.api.update_social(data)
            QMessageBox.information(self, "Guardado", "Redes sociales actualizadas.")
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{e}")

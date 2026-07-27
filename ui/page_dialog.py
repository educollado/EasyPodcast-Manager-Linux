import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QDialogButtonBox, QScrollArea, QWidget, QMessageBox
)
from .html_editor import HtmlEditorField


class PageDialog(QDialog):
    def __init__(self, parent=None, page=None):
        super().__init__(parent)
        self.page = page or {}
        self.setWindowTitle("Editar página" if page else "Nueva página")
        self.setMinimumWidth(500)
        self.setMinimumHeight(440)
        self._build_ui()
        if page:
            self._populate(page)

    def _build_ui(self):
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form = QFormLayout(container)
        scroll.setWidget(container)
        outer.addWidget(scroll)

        self.title_edit = QLineEdit()
        form.addRow("Título*:", self.title_edit)

        self.slug_edit = QLineEdit()
        form.addRow("Slug:", self.slug_edit)

        self.content_edit = HtmlEditorField()
        self.content_edit.setMinimumHeight(280)
        form.addRow("Contenido:", self.content_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["draft", "published"])
        form.addRow("Estado:", self.status_combo)

        self.parent_id_edit = QLineEdit()
        self.parent_id_edit.setPlaceholderText("ID de la página padre (opcional)")
        form.addRow("Página padre:", self.parent_id_edit)

        self.sort_order_edit = QLineEdit()
        self.sort_order_edit.setPlaceholderText("0")
        form.addRow("Orden en menú:", self.sort_order_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _populate(self, page):
        self.title_edit.setText(page.get("title", ""))
        self.slug_edit.setText(page.get("slug", ""))
        self.content_edit.setPlainText(page.get("content", ""))
        idx = self.status_combo.findText(page.get("status", "draft"))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        parent_id = page.get("parent_id")
        self.parent_id_edit.setText("" if parent_id in (None, "") else str(parent_id))
        sort_order = page.get("sort_order", page.get("menu_order"))
        self.sort_order_edit.setText("" if sort_order in (None, "") else str(sort_order))

    def _on_accept(self):
        missing = []
        title = self.title_edit.text().strip()
        slug = self.slug_edit.text().strip()
        parent_id = self.parent_id_edit.text().strip()

        if not title:
            missing.append("Título")
        if not slug:
            missing.append("Slug")
        if missing:
            QMessageBox.warning(
                self,
                "Campos obligatorios",
                "Faltan campos obligatorios:\n• " + "\n• ".join(missing),
            )
            return
        if re.fullmatch(r"[a-z0-9-]+", slug) is None:
            QMessageBox.warning(
                self,
                "Slug no válido",
                "El slug solo puede contener letras minúsculas, números y guiones.",
            )
            return
        if parent_id and (not parent_id.isdigit() or int(parent_id) <= 0):
            QMessageBox.warning(
                self,
                "Página padre no válida",
                "La página padre debe ser un ID numérico positivo.",
            )
            return
        current_id = str(self.page.get("id") or "")
        if parent_id and parent_id == current_id:
            QMessageBox.warning(
                self,
                "Página padre no válida",
                "Una página no puede ser su propia página padre.",
            )
            return
        self.accept()

    def get_data(self):
        data = {
            "title": self.title_edit.text().strip(),
            "slug": self.slug_edit.text().strip(),
            "content": self.content_edit.toPlainText().strip(),
            "status": self.status_combo.currentText(),
        }
        parent_id = self.parent_id_edit.text().strip()
        if parent_id.isdigit() and int(parent_id) > 0:
            data["parent_id"] = int(parent_id)
        elif self.page:
            data["parent_id"] = None
        order = self.sort_order_edit.text().strip()
        if order.lstrip("-").isdigit():
            data["sort_order"] = int(order)
        if self.page.get("full_path"):
            data["current_full_path"] = self.page["full_path"]
        return {k: v for k, v in data.items() if v != ""}

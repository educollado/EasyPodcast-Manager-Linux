from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from api import APIError
from .page_dialog import PageDialog


class PagesTab(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._pages = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.btn_new = QPushButton("Nueva")
        self.btn_edit = QPushButton("Editar")
        self.btn_delete = QPushButton("Borrar")
        self.btn_refresh = QPushButton("Actualizar")
        for btn in (self.btn_new, self.btn_edit, self.btn_delete, self.btn_refresh):
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Título", "Slug", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        self.btn_new.clicked.connect(self._on_new)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_refresh.clicked.connect(self.refresh)

    def refresh(self):
        try:
            result = self.api.get_pages()
            if isinstance(result, list):
                self._pages = result
            else:
                self._pages = result.get("items", result.get("pages", []))
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las páginas:\n{e}")
            return

        self.table.setRowCount(0)
        for page in self._pages:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(page.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(page.get("title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(page.get("slug", "")))
            self.table.setItem(row, 3, QTableWidgetItem(page.get("status", "")))

    def _selected_page(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._pages):
            return None
        return self._pages[row]

    def _on_new(self):
        dlg = PageDialog(self)
        if dlg.exec() == PageDialog.DialogCode.Accepted:
            try:
                self.api.create_page(dlg.get_data())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la página:\n{e}")

    def _on_edit(self):
        page = self._selected_page()
        if not page:
            QMessageBox.information(self, "Sin selección", "Selecciona una página primero.")
            return
        try:
            full_page = self.api.get_page(page["id"])
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la página:\n{e}")
            return
        dlg = PageDialog(self, full_page)
        if dlg.exec() == PageDialog.DialogCode.Accepted:
            try:
                self.api.update_page(page["id"], dlg.get_data())
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar la página:\n{e}")

    def _on_delete(self):
        page = self._selected_page()
        if not page:
            QMessageBox.information(self, "Sin selección", "Selecciona una página primero.")
            return
        reply = QMessageBox.question(
            self, "Confirmar borrado",
            f"¿Borrar la página \"{page.get('title', '')}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api.delete_page(page["id"])
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Error", f"No se pudo borrar la página:\n{e}")

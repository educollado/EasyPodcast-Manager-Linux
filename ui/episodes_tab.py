from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLabel, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from api import APIError
from .episode_dialog import EpisodeDialog


class NumericItem(QTableWidgetItem):
    """QTableWidgetItem que ordena numéricamente."""
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)


class EpisodesTab(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._episodes = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Filtrar:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "published", "draft"])
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.filter_combo)
        toolbar.addStretch()

        self.btn_new = QPushButton("Nuevo")
        self.btn_edit = QPushButton("Editar")
        self.btn_toggle = QPushButton("Publicar/Borrador")
        self.btn_delete = QPushButton("Borrar")
        self.btn_refresh = QPushButton("Actualizar")

        for btn in (self.btn_new, self.btn_edit, self.btn_toggle, self.btn_delete, self.btn_refresh):
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Temporada", "Número", "Título", "Estado", "Fecha"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        # Connections
        self.btn_new.clicked.connect(self._on_new)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_toggle.clicked.connect(self._on_toggle)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_refresh.clicked.connect(self.refresh)

    def refresh(self):
        status_filter = self.filter_combo.currentText()
        status = None if status_filter == "Todos" else status_filter
        try:
            result = self.api.get_episodes(status=status)
            # Support both list and dict with 'data' key
            if isinstance(result, list):
                self._episodes = result
            else:
                self._episodes = result.get("items", result.get("episodes", []))
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar episodios:\n{e}")
            return

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for ep in self._episodes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, NumericItem(str(ep.get("season_number", "") or "")))
            self.table.setItem(row, 1, NumericItem(str(ep.get("episode_number", "") or "")))
            title_item = QTableWidgetItem(ep.get("title", ""))
            title_item.setData(Qt.ItemDataRole.UserRole, ep.get("id"))
            self.table.setItem(row, 2, title_item)
            self.table.setItem(row, 3, QTableWidgetItem(ep.get("status", "")))
            pub = ep.get("pub_date") or ep.get("published_at") or ep.get("created_at", "")
            self.table.setItem(row, 4, QTableWidgetItem(str(pub)[:10] if pub else ""))
        self.table.setSortingEnabled(True)

    def _selected_episode(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        title_item = self.table.item(row, 2)
        if not title_item:
            return None
        ep_id = title_item.data(Qt.ItemDataRole.UserRole)
        return next((e for e in self._episodes if e.get("id") == ep_id), None)

    def _on_new(self):
        defaults = {}
        if self._episodes:
            last = max(self._episodes, key=lambda e: e.get("episode_number") or 0)
            defaults["season_number"] = last.get("season_number") or 1
            defaults["episode_number"] = (last.get("episode_number") or 0) + 1
        dlg = EpisodeDialog(self, defaults=defaults)
        if dlg.exec() == EpisodeDialog.DialogCode.Accepted:
            data = dlg.get_data()
            files = dlg.get_files()
            try:
                self.api.create_episode(data, audio_path=files["audio"], image_path=files["image"])
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el episodio:\n{e}")

    def _on_edit(self):
        ep = self._selected_episode()
        if not ep:
            QMessageBox.information(self, "Sin selección", "Selecciona un episodio primero.")
            return
        try:
            full_ep = self.api.get_episode(ep["id"])
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el episodio:\n{e}")
            return
        dlg = EpisodeDialog(self, full_ep)
        if dlg.exec() == EpisodeDialog.DialogCode.Accepted:
            data = dlg.get_data()
            files = dlg.get_files()
            try:
                self.api.update_episode(ep["id"], data, audio_path=files["audio"], image_path=files["image"])
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el episodio:\n{e}")

    def _on_toggle(self):
        ep = self._selected_episode()
        if not ep:
            QMessageBox.information(self, "Sin selección", "Selecciona un episodio primero.")
            return
        new_status = "draft" if ep.get("status") == "published" else "published"
        try:
            self.api.update_episode(ep["id"], {"status": new_status})
            self.refresh()
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo cambiar el estado:\n{e}")

    def _on_delete(self):
        ep = self._selected_episode()
        if not ep:
            QMessageBox.information(self, "Sin selección", "Selecciona un episodio primero.")
            return
        reply = QMessageBox.question(
            self, "Confirmar borrado",
            f"¿Borrar el episodio \"{ep.get('title', '')}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api.delete_episode(ep["id"])
                self.refresh()
            except APIError as e:
                QMessageBox.critical(self, "Error", f"No se pudo borrar el episodio:\n{e}")

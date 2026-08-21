from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDialogButtonBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from urllib.parse import urlparse
import config
from api import EasyPodcastAPI, APIError


class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de EasyPodcast")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._profile_id = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "<b>Bienvenido a EasyPodcast</b><br>"
            "Configura uno o varios podcasts y cambia entre ellos desde la ventana principal."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        profile_row = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._load_selected_profile)
        profile_row.addWidget(self.profile_combo, 1)
        self.btn_new = QPushButton("Nuevo")
        self.btn_new.clicked.connect(self._new_profile)
        profile_row.addWidget(self.btn_new)
        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.clicked.connect(self._delete_profile)
        profile_row.addWidget(self.btn_delete)
        layout.addLayout(profile_row)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("A Ratos Podcast")
        form.addRow("Nombre del perfil:", self.name_edit)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.mipodcast.com/directorio")
        form.addRow("URL del podcast:", self.url_edit)

        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setPlaceholderText("Token de API")
        form.addRow("Token de API:", self.token_edit)
        layout.addLayout(form)

        url_help = QLabel(
            "Incluye el directorio del podcast. Ejemplo: "
            "<code>https://www.aratospodcast.com/aratos</code>"
        )
        url_help.setWordWrap(True)
        layout.addWidget(url_help)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._reload_profiles()

    def _reload_profiles(self, selected_id=None):
        active = config.get_active_profile()
        selected_id = selected_id or (active["id"] if active else None)
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in config.get_profiles():
            self.profile_combo.addItem(profile["name"], profile["id"])
        index = self.profile_combo.findData(selected_id)
        self.profile_combo.setCurrentIndex(index if index >= 0 else 0)
        self.profile_combo.blockSignals(False)
        if self.profile_combo.count():
            self._load_selected_profile(self.profile_combo.currentIndex())
        else:
            self._new_profile()

    def _load_selected_profile(self, index):
        profile_id = self.profile_combo.itemData(index) if index >= 0 else None
        profile = next(
            (item for item in config.get_profiles() if item["id"] == profile_id),
            None,
        )
        if not profile:
            return
        self._profile_id = profile["id"]
        self.name_edit.setText(profile["name"])
        self.url_edit.setText(profile["base_url"])
        self.token_edit.setText(profile["token"])
        self.btn_delete.setEnabled(True)

    def _new_profile(self):
        self._profile_id = None
        self.profile_combo.setCurrentIndex(-1)
        self.name_edit.clear()
        self.url_edit.clear()
        self.token_edit.clear()
        self.btn_delete.setEnabled(False)
        self.name_edit.setFocus()

    def _delete_profile(self):
        if not self._profile_id:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar perfil",
            f"¿Eliminar el perfil «{self.name_edit.text().strip()}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        config.delete_profile(self._profile_id)
        self._profile_id = None
        self._reload_profiles()

    def _on_accept(self):
        name = self.name_edit.text().strip()
        base_url = self.url_edit.text().strip()
        token = self.token_edit.text().strip()

        if not name or not base_url or not token:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Debes introducir el nombre, la URL del podcast y el token.",
            )
            return

        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            QMessageBox.warning(
                self, "URL inválida", "Introduce una URL completa que empiece por http:// o https://"
            )
            return

        # Test connection
        try:
            api = EasyPodcastAPI(base_url, token)
            api.get_podcast()
        except APIError as e:
            QMessageBox.critical(self, "Error de conexión", f"No se pudo conectar:\n{e}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado:\n{e}")
            return

        self._profile_id = config.save_profile(
            name, base_url, token, profile_id=self._profile_id, make_active=True
        )
        self.accept()

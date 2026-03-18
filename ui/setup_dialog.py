from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
import config
from api import EasyPodcastAPI, APIError


class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de EasyPodcast")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "<b>Bienvenido a EasyPodcast</b><br>"
            "Introduce la URL de tu podcast y el token de API para continuar."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        form = QFormLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.mipodcast.com")
        form.addRow("URL del podcast:", self.url_edit)

        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setPlaceholderText("Token de API")
        form.addRow("Token de API:", self.token_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Pre-fill if config exists
        base_url, token = config.get_credentials()
        if base_url:
            self.url_edit.setText(base_url)
        if token:
            self.token_edit.setText(token)

    def _on_accept(self):
        base_url = self.url_edit.text().strip()
        token = self.token_edit.text().strip()

        if not base_url or not token:
            QMessageBox.warning(self, "Datos incompletos", "Debes introducir la URL y el token.")
            return

        if not base_url.startswith("http"):
            QMessageBox.warning(self, "URL inválida", "La URL debe empezar por http:// o https://")
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

        config.save_credentials(base_url, token)
        self.accept()

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QMenuBar, QMessageBox,
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

import config
from api import EasyPodcastAPI
from .episodes_tab import EpisodesTab
from .podcast_tab import PodcastTab
from .pages_tab import PagesTab
from .social_tab import SocialTab
from .tools_tab import ToolsTab
from .setup_dialog import SetupDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyPodcast Manager")
        self.setMinimumSize(900, 600)
        self.api = None
        self._setup_menu()
        self._setup_statusbar()
        self._load_api()
        self._build_tabs()

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&Archivo")
        act_quit = QAction("&Salir", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        prefs_menu = menubar.addMenu("&Preferencias")
        act_setup = QAction("&Configuración...", self)
        act_setup.triggered.connect(self._open_setup)
        prefs_menu.addAction(act_setup)

        help_menu = menubar.addMenu("&Ayuda")
        act_updates = QAction("&Comprobar actualizaciones...", self)
        act_updates.triggered.connect(self._check_updates)
        help_menu.addAction(act_updates)
        help_menu.addSeparator()
        act_about = QAction("&Acerca de", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def _load_api(self):
        base_url, token = config.get_credentials()
        if base_url and token:
            self.api = EasyPodcastAPI(base_url, token)
            self.status.showMessage(f"Conectado a: {base_url}")
        else:
            self.api = None
            self.status.showMessage("Sin configurar")

    def _build_tabs(self):
        if self.api is None:
            return
        tabs = QTabWidget()
        tabs.addTab(EpisodesTab(self.api), "Episodios")
        tabs.addTab(PodcastTab(self.api), "Podcast")
        tabs.addTab(PagesTab(self.api), "Páginas")
        tabs.addTab(SocialTab(self.api), "Redes Sociales")
        tabs.addTab(ToolsTab(self.api), "Herramientas")
        self.setCentralWidget(tabs)

    def _open_setup(self):
        dlg = SetupDialog(self)
        if dlg.exec() == SetupDialog.DialogCode.Accepted:
            self._load_api()
            self._build_tabs()

    def _check_updates(self):
        if not self.api:
            return
        from api import APIError
        try:
            data = self.api.get_system_version()
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo consultar la versión:\n{e}")
            return
        current = data.get("current_version", "?")
        latest = data.get("latest_version", "?")
        available = data.get("update_available", False)
        fetch_error = data.get("fetch_error", "")
        if fetch_error:
            QMessageBox.warning(self, "Actualizaciones", f"Versión actual: {current}\nNo se pudo contactar con GitHub.")
        elif available:
            QMessageBox.information(self, "Actualización disponible",
                f"Versión actual: {current}\nNueva versión: {latest}\n\n"
                "Ve a Herramientas para actualizar el servidor.")
        else:
            QMessageBox.information(self, "Actualizaciones", f"El servidor está al día (v{current}).")

    def _show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Acerca de EasyPodcast Manager")
        dlg.setMinimumWidth(340)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)

        version_text = ""
        if self.api:
            try:
                data = self.api.get_system_version()
                current = data.get("current_version", "?")
                version_text = f"<br>Versión del servidor: {current}"
            except Exception:
                version_text = "<br>Versión del servidor: ?"

        label = QLabel(
            "<b style='font-size:15px;'>EasyPodcast Manager</b><br><br>"
            "Cliente de escritorio para KDE/Linux.<br>"
            "Gestiona tu podcast desde el escritorio.<br><br>"
            "Software libre — "
            "<a href='https://www.easypodcast.eu'>https://www.easypodcast.eu</a>"
            f"<br>Versión del cliente: 0.0.4"
            f"{version_text}"
        )
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)

        dlg.exec()

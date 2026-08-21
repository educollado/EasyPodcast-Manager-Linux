from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QMenuBar, QMessageBox,
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QToolBar, QComboBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

import config
from api import EasyPodcastAPI
from client_version import CLIENT_VERSION
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
        self._setup_profile_toolbar()
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

    def _setup_profile_toolbar(self):
        toolbar = QToolBar("Podcasts", self)
        toolbar.setMovable(False)
        toolbar.addWidget(QLabel("Podcast: "))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(220)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        toolbar.addWidget(self.profile_combo)
        self.addToolBar(toolbar)

    def _refresh_profile_selector(self):
        active = config.get_active_profile()
        active_id = active["id"] if active else None
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in config.get_profiles():
            self.profile_combo.addItem(profile["name"], profile["id"])
        index = self.profile_combo.findData(active_id)
        self.profile_combo.setCurrentIndex(index if index >= 0 else -1)
        self.profile_combo.setEnabled(self.profile_combo.count() > 1)
        self.profile_combo.blockSignals(False)

    def _on_profile_changed(self, index):
        profile_id = self.profile_combo.itemData(index)
        if not profile_id or not config.set_active_profile(profile_id):
            return
        self._load_api()
        self._build_tabs()

    def _load_api(self):
        self._refresh_profile_selector()
        profile = config.get_active_profile()
        if profile:
            self.api = EasyPodcastAPI(profile["base_url"], profile["token"])
            self.status.showMessage(
                f"Conectado a: {profile['name']} — {profile['base_url']}"
            )
        else:
            self.api = None
            self.status.showMessage("Sin configurar")

    def _build_tabs(self):
        if self.api is None:
            empty = QLabel("Configura un podcast para comenzar.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setCentralWidget(empty)
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
            f"<br>Versión del cliente: {CLIENT_VERSION}"
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

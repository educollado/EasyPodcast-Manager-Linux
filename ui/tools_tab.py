from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from api import APIError


class ToolsTab(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Tools group
        tools_group = QGroupBox("Herramientas")
        tools_layout = QHBoxLayout(tools_group)

        self.btn_cache = QPushButton("Limpiar caché")
        self.btn_feed = QPushButton("Regenerar feed")
        self.btn_images = QPushButton("Regenerar imágenes")
        self.btn_stats = QPushButton("Ver estadísticas")

        self.btn_cache.clicked.connect(self._on_clear_cache)
        self.btn_feed.clicked.connect(self._on_regen_feed)
        self.btn_images.clicked.connect(self._on_regen_images)
        self.btn_stats.clicked.connect(self._on_stats)

        for btn in (self.btn_cache, self.btn_feed, self.btn_images, self.btn_stats):
            btn.setMinimumWidth(160)
            btn.setMinimumHeight(40)
            tools_layout.addWidget(btn)

        tools_layout.addStretch()
        layout.addWidget(tools_group)

        # Update group
        update_group = QGroupBox("Actualización del servidor")
        update_layout = QHBoxLayout(update_group)

        self.btn_check_update = QPushButton("Comprobar actualizaciones")
        self.btn_check_update.setMinimumWidth(200)
        self.btn_check_update.setMinimumHeight(40)
        self.btn_check_update.clicked.connect(self._on_check_update)
        update_layout.addWidget(self.btn_check_update)

        self.btn_do_update = QPushButton("Actualizar servidor")
        self.btn_do_update.setMinimumWidth(160)
        self.btn_do_update.setMinimumHeight(40)
        self.btn_do_update.setEnabled(False)
        self.btn_do_update.clicked.connect(self._on_do_update)
        update_layout.addWidget(self.btn_do_update)

        self.version_label = QLabel("")
        self.version_label.setStyleSheet("color: #5f544d; padding-left: 8px;")
        update_layout.addWidget(self.version_label)
        update_layout.addStretch()
        layout.addWidget(update_group)

        # Stats / output area
        stats_group = QGroupBox("Estadísticas / Resultado")
        stats_layout = QVBoxLayout(stats_group)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(200)
        stats_layout.addWidget(self.output)
        layout.addWidget(stats_group)

    # Traducciones de claves de la API a etiquetas legibles
    _LABELS = {
        "total_episodes":      "Episodios totales",
        "published_episodes":  "Publicados",
        "draft_episodes":      "Borradores",
        "episodes_count":      "Episodios",
        "total_plays":         "Reproducciones",
        "total_downloads":     "Descargas totales",
        "total_pages":         "Páginas",
        "pages_count":         "Páginas",
        "total_size_bytes":    "Tamaño total",
        "feed_size":           "Tamaño del feed",
        "cache_hits":          "Aciertos de caché",
        "last_updated":        "Última actualización",
        "last_build":          "Última generación",
        "version":             "Versión",
    }

    def _fmt_value(self, key, val):
        """Formatea un valor de estadística para mostrarlo al usuario."""
        if isinstance(val, bool):
            return "Sí" if val else "No"
        if key.endswith("_bytes") and isinstance(val, (int, float)):
            for unit in ("B", "KB", "MB", "GB"):
                if val < 1024:
                    return f"{val:.1f} {unit}"
                val /= 1024
            return f"{val:.1f} TB"
        if isinstance(val, int):
            return f"{val:,}".replace(",", ".")
        if isinstance(val, float):
            return f"{val:,.1f}".replace(",", ".")
        return str(val)

    def _card(self, label, display, wide=False, is_number=True):
        """Genera HTML de una tarjeta de estadística."""
        min_width = "300px" if wide else "140px"
        value_style = (
            "font-size:22px; font-weight:bold; color:#8c3509;"
            if is_number else
            "font-size:14px; color:#333;"
        )
        return f"""
        <div style="
            display:inline-block; min-width:{min_width}; margin:6px;
            background:#fdf6f0; border:1px solid #e0cfc5;
            border-radius:6px; padding:12px 16px; vertical-align:top;
        ">
            <div style="{value_style}">{display}</div>
            <div style="font-size:11px; color:#888; margin-top:4px;">{label}</div>
        </div>"""

    def _section_header(self, title):
        return (
            f"<p style='font-size:12px; color:#5f544d; margin:12px 6px 4px 6px;'>"
            f"<b>{title}</b></p>"
        )

    def _show_stats(self, data):
        """Muestra estadísticas en tarjetas HTML."""
        if not isinstance(data, dict) or not data:
            self.output.setHtml(
                "<p style='color:#888; font-style:italic; margin:12px;'>Sin datos.</p>"
            )
            return

        html = ""

        # --- Sección Episodios ---
        ep = data.get("episodes")
        if isinstance(ep, dict):
            html += self._section_header("Episodios")
            html += self._card("Publicados", self._fmt_value("published", ep.get("published", 0)))
            html += self._card("Borradores", self._fmt_value("drafts", ep.get("drafts", 0)))
            html += self._card("Total", self._fmt_value("total", ep.get("total", 0)))
            size = ep.get("audio_size_bytes")
            if size is not None:
                html += self._card("Tamaño de audios", self._fmt_value("audio_size_bytes", size))
            last_title = ep.get("last_title", "")
            last_date = ep.get("last_pub_date", "")
            if last_title:
                text = last_title
                if last_date:
                    text += f"<br><span style='font-size:11px;color:#888;'>{last_date}</span>"
                html += self._card("Último publicado", text, wide=True, is_number=False)

        # --- Sección Caché ---
        cache = data.get("cache")
        if isinstance(cache, dict):
            html += self._section_header("Caché")
            enabled = cache.get("enabled", False)
            html += self._card("Estado", "Activa" if enabled else "Inactiva", is_number=False)
            files = cache.get("files")
            if files is not None:
                html += self._card("Páginas en caché", self._fmt_value("files", files))
            size = cache.get("size_bytes")
            if size is not None:
                html += self._card("Tamaño de caché", self._fmt_value("size_bytes", size))

        # --- Sección Descargas y reproducciones ---
        downloads = data.get("downloads")
        if isinstance(downloads, dict):
            daily = downloads.get("daily", {})
            summary = downloads.get("summary", {})
            daily_items = daily.get("items", []) if isinstance(daily, dict) else []
            summary_items = summary.get("items", []) if isinstance(summary, dict) else []

            event_total = daily.get("total", len(daily_items)) if isinstance(daily, dict) else 0
            downloads_total = sum(
                1 for item in daily_items
                if item.get("action_type", "download") == "download"
            )
            plays_total = sum(
                1 for item in daily_items
                if item.get("action_type") == "play"
            )
            tracked_episodes = (
                summary.get("total", len(summary_items))
                if isinstance(summary, dict) else 0
            )
            all_time_downloads = sum(
                int(item.get("total_downloads") or 0) for item in summary_items
            )

            html += self._section_header("Descargas y reproducciones")
            html += self._card(
                "Eventos registrados", self._fmt_value("events", event_total)
            )
            html += self._card(
                "Descargas recientes", self._fmt_value("downloads", downloads_total)
            )
            html += self._card(
                "Reproducciones recientes", self._fmt_value("plays", plays_total)
            )
            html += self._card(
                "Episodios con actividad",
                self._fmt_value("episodes", tracked_episodes),
            )
            html += self._card(
                "Descargas acumuladas",
                self._fmt_value("downloads", all_time_downloads),
            )

        # --- Fallback: claves simples de primer nivel ---
        simple_keys = {k: v for k, v in data.items()
                       if not isinstance(v, dict) and k not in ("episodes", "cache")}
        if simple_keys:
            if html:
                html += self._section_header("Otros")
            for key, val in simple_keys.items():
                label = self._LABELS.get(key, key.replace("_", " ").capitalize())
                display = self._fmt_value(key, val)
                is_number = isinstance(val, (int, float)) and not isinstance(val, bool)
                html += self._card(label, display, is_number=is_number)

        if not html:
            html = "<p style='color:#888; font-style:italic; margin:12px;'>Sin datos reconocibles.</p>"

        self.output.setHtml(f"""
        <html><body style="font-family:sans-serif; margin:8px;">
            <p style="font-size:12px; color:#5f544d; margin-bottom:4px;">
                <b>Estadísticas del podcast</b>
            </p>
            {html}
        </body></html>
        """)

    def _show_result(self, data):
        self._show_stats(data)

    def _show_ok(self, message):
        self.output.setHtml(f"""
        <html><body style="font-family:sans-serif; margin:12px;">
            <div style="
                background:#eaf4ea; border:1px solid #a8d5a2;
                border-radius:6px; padding:12px 16px; color:#2d6a2d;
                font-size:13px;
            ">&#10003; &nbsp;{message}</div>
        </body></html>
        """)

    def _on_clear_cache(self):
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Limpiar la caché del servidor?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api.clear_cache()
            self._show_ok("Caché limpiada correctamente.")
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo limpiar la caché:\n{e}")

    def _on_regen_feed(self):
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Regenerar el feed RSS?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api.regenerate_feed()
            self._show_ok("Feed RSS regenerado correctamente.")
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo regenerar el feed:\n{e}")

    def _on_regen_images(self):
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Regenerar las imágenes del podcast?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api.regenerate_images()
            self._show_ok("Imágenes regeneradas correctamente.")
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudieron regenerar las imágenes:\n{e}")

    def _on_stats(self):
        try:
            result = self.api.get_stats()
            self._show_result(result)
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudieron obtener estadísticas:\n{e}")

    def _on_check_update(self):
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
            self.version_label.setText(f"v{current}  ·  error al consultar GitHub")
            self.btn_do_update.setEnabled(False)
            return

        if available:
            self.version_label.setText(f"v{current}  →  v{latest} disponible")
            self.version_label.setStyleSheet("color: #8c3509; font-weight: bold; padding-left: 8px;")
            self.btn_do_update.setEnabled(True)
        else:
            self.version_label.setText(f"v{current}  ·  al día")
            self.version_label.setStyleSheet("color: #5f544d; padding-left: 8px;")
            self.btn_do_update.setEnabled(False)

    def _on_do_update(self):
        reply = QMessageBox.warning(
            self, "Actualizar servidor",
            "Esta operación descargará e instalará la última versión desde GitHub.\n"
            "Es irreversible. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            data = self.api.system_update()
            msg = data.get("message", "")
            updated_from = data.get("updated_from", "?")
            updated_to = data.get("updated_to", "?")
            self._show_ok(
                f"Actualización completada: v{updated_from} &rarr; v{updated_to}."
                + (f"<br><span style='font-size:11px;color:#2d6a2d;'>{msg}</span>" if msg else "")
            )
            self.version_label.setText(f"v{updated_to}  ·  al día")
            self.version_label.setStyleSheet("color: #5f544d; padding-left: 8px;")
            self.btn_do_update.setEnabled(False)
        except APIError as e:
            if e.status_code == 403:
                detail = (
                    "El servidor rechazó la actualización. Esta operación requiere "
                    "un token de API con alcance «admin»."
                )
            else:
                detail = f"No se pudo actualizar:\n{e}"
            QMessageBox.critical(self, "Error", detail)

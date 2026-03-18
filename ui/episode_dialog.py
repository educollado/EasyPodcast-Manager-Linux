from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QDialogButtonBox, QLabel, QScrollArea, QWidget,
    QHBoxLayout, QPushButton, QFileDialog
)
import os
from PySide6.QtCore import Qt
from .image_preview import ImagePreviewField
from .audio_player import AudioPlayerField
from .audio_recorder import RecorderDialog
from .html_editor import HtmlEditorField


class EpisodeDialog(QDialog):
    def __init__(self, parent=None, episode=None, defaults=None):
        super().__init__(parent)
        self.episode = episode or {}
        self._audio_path = None
        self._image_path = None
        self.setWindowTitle("Editar episodio" if episode else "Nuevo episodio")
        self.setMinimumWidth(560)
        self.setMinimumHeight(500)
        self._build_ui()
        if episode:
            self._populate(episode)
        elif defaults:
            self._apply_defaults(defaults)

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

        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(100)
        form.addRow("Descripción*:", self.description_edit)

        self.content_edit = HtmlEditorField()
        self.content_edit.setMinimumHeight(220)
        form.addRow("Contenido:", self.content_edit)

        # --- Audio ---
        audio_container = QWidget()
        audio_layout = QVBoxLayout(audio_container)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        audio_layout.setSpacing(4)

        self.audio_url_edit = AudioPlayerField("URL del audio (https://...)")
        audio_layout.addWidget(self.audio_url_edit)

        audio_file_row = QHBoxLayout()
        self.btn_browse_audio = QPushButton("Seleccionar archivo...")
        self.btn_browse_audio.clicked.connect(self._browse_audio)
        audio_file_row.addWidget(self.btn_browse_audio)
        self.btn_record_audio = QPushButton("⏺  Grabar")
        self.btn_record_audio.clicked.connect(self._record_audio)
        audio_file_row.addWidget(self.btn_record_audio)
        self.audio_file_label = QLabel("")
        self.audio_file_label.setStyleSheet("color: #5f544d; font-size: 11px;")
        audio_file_row.addWidget(self.audio_file_label, 1)
        audio_layout.addLayout(audio_file_row)

        form.addRow("Audio:", audio_container)

        # --- Imagen ---
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(4)

        self.image_url_edit = ImagePreviewField("URL de la imagen (https://...)")
        image_layout.addWidget(self.image_url_edit)

        image_file_row = QHBoxLayout()
        self.btn_browse_image = QPushButton("Seleccionar imagen...")
        self.btn_browse_image.clicked.connect(self._browse_image)
        image_file_row.addWidget(self.btn_browse_image)
        self.image_file_label = QLabel("")
        self.image_file_label.setStyleSheet("color: #5f544d; font-size: 11px;")
        image_file_row.addWidget(self.image_file_label, 1)
        image_layout.addLayout(image_file_row)

        form.addRow("Imagen:", image_container)

        # --- Resto de campos ---
        self.duration_edit = QLineEdit()
        self.duration_edit.setPlaceholderText("HH:MM:SS")
        form.addRow("Duración:", self.duration_edit)

        self.season_edit = QLineEdit()
        form.addRow("Temporada:", self.season_edit)

        self.episode_num_edit = QLineEdit()
        form.addRow("Número:", self.episode_num_edit)

        self.episode_type_combo = QComboBox()
        self.episode_type_combo.addItems(["full", "trailer", "bonus"])
        form.addRow("Tipo:", self.episode_type_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["draft", "published"])
        form.addRow("Estado:", self.status_combo)

        self.published_at_edit = QLineEdit()
        self.published_at_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        form.addRow("Fecha publicación:", self.published_at_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _record_audio(self):
        dlg = RecorderDialog(self)
        if dlg.exec() == RecorderDialog.DialogCode.Accepted:
            path = dlg.get_path()
            if path:
                self._audio_path = path
                self.audio_file_label.setText(os.path.basename(path))
                self.audio_url_edit.setText("")
                self._fill_duration(path)

    def _browse_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar audio",
            "", "Audio (*.mp3 *.ogg *.m4a *.wav *.flac);;Todos los archivos (*)"
        )
        if path:
            self._audio_path = path
            self.audio_file_label.setText(path.split("/")[-1])
            self.audio_url_edit.setText("")
            self._fill_duration(path)

    def _fill_duration(self, path):
        total = None
        try:
            from mutagen import File as MutagenFile
            audio = MutagenFile(path)
            if audio and audio.info:
                total = int(audio.info.length)
        except Exception:
            pass
        if total is None:
            try:
                import subprocess, json
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", path],
                    capture_output=True
                )
                info = json.loads(r.stdout)
                total = int(float(info["format"]["duration"]))
            except Exception:
                pass
        if total is not None:
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
            self.duration_edit.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen",
            "", "Imágenes (*.jpg *.jpeg *.png *.webp);;Todos los archivos (*)"
        )
        if path:
            self._image_path = path
            self.image_file_label.setText(path.split("/")[-1])
            self.image_url_edit.setText("")

    def _on_accept(self):
        missing = []
        if not self.title_edit.text().strip():
            missing.append("Título")
        if not self.description_edit.toPlainText().strip():
            missing.append("Descripción")
        if not self.audio_url_edit.text().strip() and not self._audio_path:
            missing.append("Audio (URL o archivo)")
        if missing:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Campos obligatorios",
                f"Faltan campos obligatorios:\n• " + "\n• ".join(missing)
            )
            return
        self.accept()

    def _apply_defaults(self, defaults):
        if "season_number" in defaults:
            self.season_edit.setText(str(defaults["season_number"]))
        if "episode_number" in defaults:
            self.episode_num_edit.setText(str(defaults["episode_number"]))

    def _populate(self, episode):
        self.title_edit.setText(episode.get("title", ""))
        self.slug_edit.setText(episode.get("slug", ""))
        self.description_edit.setPlainText(episode.get("description", ""))
        self.content_edit.setPlainText(episode.get("content", ""))
        self.audio_url_edit.setText(episode.get("audio_url", ""))
        self.image_url_edit.setText(episode.get("image_url", ""))
        self.duration_edit.setText(str(episode.get("duration", "")))
        self.season_edit.setText(str(episode.get("season_number", "") or ""))
        self.episode_num_edit.setText(str(episode.get("episode_number", "") or ""))

        ep_type = episode.get("episode_type", "full")
        idx = self.episode_type_combo.findText(ep_type)
        if idx >= 0:
            self.episode_type_combo.setCurrentIndex(idx)

        status = episode.get("status", "draft")
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        self.published_at_edit.setText(str(episode.get("pub_date") or episode.get("published_at") or ""))

    def get_data(self):
        data = {
            "title": self.title_edit.text().strip(),
            "slug": self.slug_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "content": self.content_edit.toPlainText().strip(),
            "audio_url": self.audio_url_edit.text().strip(),
            "image_url": self.image_url_edit.text().strip(),
            "duration": self.duration_edit.text().strip(),
            "episode_type": self.episode_type_combo.currentText(),
            "status": self.status_combo.currentText(),
            "published_at": self.published_at_edit.text().strip(),
        }
        season = self.season_edit.text().strip()
        if season.isdigit():
            data["season_number"] = int(season)
        ep_num = self.episode_num_edit.text().strip()
        if ep_num.isdigit():
            data["episode_number"] = int(ep_num)
        return {k: v for k, v in data.items() if v != ""}

    def get_files(self):
        """Devuelve rutas de archivo seleccionadas, o None si no se seleccionó."""
        return {
            "audio": self._audio_path,
            "image": self._image_path,
        }

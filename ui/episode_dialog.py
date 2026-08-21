from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QDialogButtonBox, QLabel, QScrollArea, QWidget,
    QHBoxLayout, QPushButton, QFileDialog
)
import os
import mimetypes
import requests
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

        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(100)
        form.addRow("Descripción:", self.description_edit)

        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Hereda el autor del podcast si se deja vacío")
        form.addRow("Autor:", self.author_edit)

        self.content_label = QLabel("Contenido:")
        self.content_edit = HtmlEditorField()
        self.content_edit.setMinimumHeight(220)
        form.addRow(self.content_label, self.content_edit)

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

        self.audio_label = QLabel("Audio:")
        form.addRow(self.audio_label, audio_container)

        audio_size_container = QWidget()
        audio_size_layout = QHBoxLayout(audio_size_container)
        audio_size_layout.setContentsMargins(0, 0, 0, 0)
        self.audio_size_edit = QLineEdit()
        self.audio_size_edit.setPlaceholderText("Obligatorio para publicar desde una URL remota")
        audio_size_layout.addWidget(self.audio_size_edit)
        self.btn_probe_audio = QPushButton("Detectar desde URL")
        self.btn_probe_audio.clicked.connect(self._probe_remote_audio)
        audio_size_layout.addWidget(self.btn_probe_audio)
        form.addRow("Tamaño del audio (bytes):", audio_size_container)

        self.audio_mime_edit = QLineEdit("audio/mpeg")
        self.audio_mime_edit.setPlaceholderText("audio/mpeg")
        form.addRow("Tipo MIME del audio:", self.audio_mime_edit)

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

        self.explicit_combo = QComboBox()
        self.explicit_combo.addItem("Heredar del podcast", "")
        self.explicit_combo.addItem("No", "0")
        self.explicit_combo.addItem("Sí", "1")
        form.addRow("Contenido explícito:", self.explicit_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["draft", "published", "scheduled"])
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        form.addRow("Estado:", self.status_combo)

        self.pub_date_label = QLabel("Fecha publicación:")
        self.published_at_edit = QLineEdit()
        self.published_at_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        form.addRow(self.pub_date_label, self.published_at_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)
        self._on_status_changed(self.status_combo.currentText())

    def _on_status_changed(self, status):
        required = not self.episode or status != "draft"
        self.content_label.setText("Contenido*:" if required else "Contenido:")
        self.audio_label.setText("Audio*:" if required else "Audio:")
        if status == "scheduled":
            self.pub_date_label.setText("Fecha programada*:")
        else:
            self.pub_date_label.setText("Fecha publicación:")

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
        try:
            self.audio_size_edit.setText(str(os.path.getsize(path)))
            self.audio_mime_edit.setText(
                mimetypes.guess_type(path)[0] or "audio/mpeg"
            )
        except OSError:
            pass

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

    def _probe_remote_audio(self):
        url = self.audio_url_edit.text().strip()
        if not url:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "URL necesaria", "Introduce primero la URL remota del audio."
            )
            return

        response = None
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            if response.status_code == 405 or not response.headers.get("Content-Length"):
                response.close()
                response = requests.get(
                    url, allow_redirects=True, timeout=10, stream=True
                )
            response.raise_for_status()
            size = response.headers.get("Content-Length", "")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
        except requests.RequestException as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "No se pudo consultar el audio",
                f"No se pudieron obtener los metadatos de la URL:\n{exc}",
            )
            return
        finally:
            if response is not None:
                response.close()

        if size.isdigit() and int(size) > 0:
            self.audio_size_edit.setText(size)
        if mime:
            self.audio_mime_edit.setText(mime)
        if not size.isdigit() or int(size) <= 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Tamaño no disponible",
                "El servidor remoto no indicó el tamaño del audio. "
                "Introdúcelo manualmente en bytes.",
            )

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
        status = self.status_combo.currentText()
        if not self.title_edit.text().strip():
            missing.append("Título")
        # La API nueva exige contenido y audio al crear, incluso como borrador.
        # Al editar se conservan los borradores antiguos incompletos.
        if not self.episode or status != "draft":
            if not self.content_edit.toPlainText().strip():
                missing.append("Contenido")
            if not self.audio_url_edit.text().strip() and not self._audio_path:
                missing.append("Audio (URL o archivo)")
            size = self.audio_size_edit.text().strip()
            if self.audio_url_edit.text().strip() and not self._audio_path:
                if not size.isdigit() or int(size) <= 0:
                    missing.append("Tamaño del audio en bytes")
        if status == "scheduled" and not self.published_at_edit.text().strip():
            missing.append("Fecha programada (obligatoria al programar)")
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
        self.description_edit.setPlainText(episode.get("description", ""))
        self.author_edit.setText(episode.get("author", "") or "")
        self.content_edit.setPlainText(episode.get("content", ""))
        self.audio_url_edit.setText(episode.get("audio_url", ""))
        self.audio_size_edit.setText(str(episode.get("audio_size_bytes", "") or ""))
        self.audio_mime_edit.setText(str(episode.get("audio_mime_type", "") or "audio/mpeg"))
        self.image_url_edit.setText(episode.get("image_url", ""))
        self.duration_edit.setText(str(episode.get("duration", "")))
        self.season_edit.setText(str(episode.get("season_number", "") or ""))
        self.episode_num_edit.setText(str(episode.get("episode_number", "") or ""))

        ep_type = episode.get("episode_type", "full")
        idx = self.episode_type_combo.findText(ep_type)
        if idx >= 0:
            self.episode_type_combo.setCurrentIndex(idx)

        explicit = episode.get("explicit", "")
        explicit = "" if explicit in (None, "") else str(int(bool(explicit))) if isinstance(explicit, bool) else str(explicit)
        idx = self.explicit_combo.findData(explicit)
        if idx >= 0:
            self.explicit_combo.setCurrentIndex(idx)

        status = episode.get("status", "draft")
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        self.published_at_edit.setText(str(episode.get("pub_date") or episode.get("published_at") or ""))

    def get_data(self):
        data = {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "author": self.author_edit.text().strip(),
            "content": self.content_edit.toPlainText().strip(),
            "audio_url": self.audio_url_edit.text().strip(),
            "audio_mime_type": self.audio_mime_edit.text().strip(),
            "image_url": self.image_url_edit.text().strip(),
            "duration": self.duration_edit.text().strip(),
            "episode_type": self.episode_type_combo.currentText(),
            "explicit": self.explicit_combo.currentData(),
            "status": self.status_combo.currentText(),
            "pub_date": self.published_at_edit.text().strip(),
        }
        season = self.season_edit.text().strip()
        if season.isdigit():
            data["season_number"] = int(season)
        ep_num = self.episode_num_edit.text().strip()
        if ep_num.isdigit():
            data["episode_number"] = int(ep_num)
        audio_size = self.audio_size_edit.text().strip()
        if audio_size.isdigit():
            data["audio_size_bytes"] = int(audio_size)
        result = {k: v for k, v in data.items() if v != ""}
        # Una cadena vacía tiene significado: restablece la herencia del podcast.
        result["explicit"] = data["explicit"]
        return result

    def get_files(self):
        """Devuelve rutas de archivo seleccionadas, o None si no se seleccionó."""
        return {
            "audio": self._audio_path,
            "image": self._image_path,
        }

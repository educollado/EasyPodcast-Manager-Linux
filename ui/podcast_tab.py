from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QScrollArea, QMessageBox, QHBoxLayout, QLabel,
    QFileDialog
)
import os
from api import APIError
from .image_preview import ImagePreviewField


class PodcastTab(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._hero_image_path = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        from PySide6.QtWidgets import QWidget as W
        container = W()
        self._form = QFormLayout(container)
        scroll.setWidget(container)
        outer.addWidget(scroll)

        def field(placeholder=""):
            e = QLineEdit()
            e.setPlaceholderText(placeholder)
            return e

        self.title_edit = field("Título del podcast")
        self._form.addRow("Título:", self.title_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(80)
        self._form.addRow("Descripción:", self.description_edit)

        self.author_edit = field("Autor")
        self._form.addRow("Autor:", self.author_edit)

        self.owner_name_edit = field("Nombre del propietario")
        self._form.addRow("Propietario:", self.owner_name_edit)

        self.email_edit = field("email@ejemplo.com")
        self._form.addRow("Email:", self.email_edit)

        self.language_edit = field("es-ES")
        self._form.addRow("Idioma:", self.language_edit)

        self.category_edit = field("Technology")
        self._form.addRow("Categoría:", self.category_edit)

        self.website_edit = field("https://...")
        self._form.addRow("Web:", self.website_edit)

        self.image_url_edit = ImagePreviewField("URL de la imagen/logo")
        self._form.addRow("Imagen:", self.image_url_edit)

        hero_container = QWidget()
        hero_layout = QVBoxLayout(hero_container)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        hero_layout.setSpacing(4)

        self.hero_image_url_edit = ImagePreviewField(
            "URL de la imagen panorámica (opcional)"
        )
        self.hero_image_url_edit.line_edit.textEdited.connect(
            self._on_hero_url_edited
        )
        hero_layout.addWidget(self.hero_image_url_edit)

        hero_file_row = QHBoxLayout()
        self.btn_browse_hero = QPushButton("Seleccionar imagen...")
        self.btn_browse_hero.clicked.connect(self._browse_hero_image)
        hero_file_row.addWidget(self.btn_browse_hero)
        self.btn_clear_hero = QPushButton("Quitar Hero")
        self.btn_clear_hero.clicked.connect(self._clear_hero)
        hero_file_row.addWidget(self.btn_clear_hero)
        self.hero_file_label = QLabel(
            "Déjala vacía para mostrar la cabecera normal."
        )
        self.hero_file_label.setStyleSheet("color: #5f544d; font-size: 11px;")
        hero_file_row.addWidget(self.hero_file_label, 1)
        hero_layout.addLayout(hero_file_row)

        self._form.addRow("Hero:", hero_container)

        self.copyright_edit = field("© 2024 ...")
        self._form.addRow("Copyright:", self.copyright_edit)

        self.explicit_edit = field("0 / 1")
        self._form.addRow("Explícito:", self.explicit_edit)

        self.type_edit = field("episodic / serial")
        self._form.addRow("Tipo:", self.type_edit)

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        self.btn_save = QPushButton("Guardar cambios")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.clicked.connect(self.refresh)
        btn_bar.addWidget(self.btn_refresh)
        btn_bar.addWidget(self.btn_save)
        outer.addLayout(btn_bar)

    def refresh(self):
        try:
            data = self.api.get_podcast()
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el podcast:\n{e}")
            return

        def s(v): return str(v) if v is not None else ""
        self.title_edit.setText(s(data.get("title")))
        self.description_edit.setPlainText(s(data.get("description")))
        self.author_edit.setText(s(data.get("author")))
        self.owner_name_edit.setText(s(data.get("owner_name")))
        self.email_edit.setText(s(data.get("owner_email")))
        self.language_edit.setText(s(data.get("language")))
        self.category_edit.setText(s(data.get("category")))
        self.website_edit.setText(s(data.get("link")))
        self.image_url_edit.setText(s(data.get("image_url")))
        self.hero_image_url_edit.setText(s(data.get("hero_image_url")))
        self._hero_image_path = None
        self.hero_file_label.setText(
            "Déjala vacía para mostrar la cabecera normal."
        )
        self.copyright_edit.setText(s(data.get("copyright")))
        self.explicit_edit.setText(s(data.get("explicit")))
        self.type_edit.setText(s(data.get("itunes_type")))

    def _on_save(self):
        data = {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "author": self.author_edit.text().strip(),
            "owner_name": self.owner_name_edit.text().strip(),
            "owner_email": self.email_edit.text().strip(),
            "language": self.language_edit.text().strip(),
            "category": self.category_edit.text().strip(),
            "link": self.website_edit.text().strip(),
            "image_url": self.image_url_edit.text().strip(),
            "hero_image_url": self.hero_image_url_edit.text().strip(),
            "copyright": self.copyright_edit.text().strip(),
            "explicit": self.explicit_edit.text().strip(),
            "itunes_type": self.type_edit.text().strip(),
        }
        try:
            if self._hero_image_path:
                updated = self.api.update_podcast(
                    data, hero_image_path=self._hero_image_path
                )
            else:
                updated = self.api.update_podcast(data)
            if isinstance(updated, dict):
                self.hero_image_url_edit.setText(
                    str(updated.get("hero_image_url") or "")
                )
            self._hero_image_path = None
            self.hero_file_label.setText(
                "Déjala vacía para mostrar la cabecera normal."
            )
            QMessageBox.information(self, "Guardado", "Metadatos del podcast actualizados.")
        except APIError as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{e}")

    def _browse_hero_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen para el Hero",
            "",
            "Imágenes (*.jpg *.jpeg *.png *.gif *.webp);;Todos los archivos (*)",
        )
        if path:
            self._hero_image_path = path
            self.hero_file_label.setText(os.path.basename(path))
            self.hero_image_url_edit.setText("")

    def _on_hero_url_edited(self, _text):
        self._hero_image_path = None
        self.hero_file_label.setText(
            "Déjala vacía para mostrar la cabecera normal."
        )

    def _clear_hero(self):
        self._hero_image_path = None
        self.hero_image_url_edit.setText("")
        self.hero_file_label.setText("El Hero se quitará al guardar.")

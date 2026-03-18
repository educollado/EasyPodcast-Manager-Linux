from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTabWidget, QTextEdit, QTextBrowser,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QLabel
)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt


class HtmlEditorField(QWidget):
    """
    Editor de HTML con dos pestañas: fuente HTML y vista previa.
    Toolbar con atajos para las etiquetas más comunes.
    API compatible con QTextEdit: toPlainText() / setPlainText().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(2)
        toolbar.setContentsMargins(0, 0, 0, 0)

        def btn(label, tooltip, width=30):
            b = QPushButton(label)
            b.setToolTip(tooltip)
            b.setFixedWidth(width)
            b.setFixedHeight(24)
            b.setStyleSheet(
                "QPushButton { border: 1px solid #c0a898; border-radius: 3px;"
                " background: #f5ede6; color: #3a2a1a; font-size: 11px;"
                " padding: 0 2px; }"
                "QPushButton:hover { background: #ead5c5; }"
                "QPushButton:pressed { background: #d4b8a5; }"
            )
            return b

        self.btn_bold   = btn("B",    "Negrita &lt;strong&gt;")
        self.btn_italic = btn("I",    "Cursiva &lt;em&gt;")
        self.btn_p      = btn("P",    "Párrafo &lt;p&gt;")
        self.btn_h2     = btn("H2",   "Encabezado H2", 34)
        self.btn_h3     = btn("H3",   "Encabezado H3", 34)
        self.btn_ul     = btn("UL",   "Lista &lt;ul&gt;", 34)
        self.btn_ol     = btn("OL",   "Lista numerada &lt;ol&gt;", 34)
        self.btn_hr     = btn("HR",   "Línea horizontal &lt;hr&gt;", 30)
        self.btn_link   = btn("URL",  "Insertar enlace &lt;a href&gt;", 36)

        sep = QLabel("|")
        sep.setStyleSheet("color:#c0a090; margin: 0 2px;")
        sep2 = QLabel("|")
        sep2.setStyleSheet("color:#c0a090; margin: 0 2px;")

        for w in (self.btn_bold, self.btn_italic, sep,
                  self.btn_h2, self.btn_h3, self.btn_p, sep2,
                  self.btn_ul, self.btn_ol, self.btn_hr, self.btn_link):
            toolbar.addWidget(w)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Pestaña HTML (fuente)
        self.source_edit = QTextEdit()
        self.source_edit.setAcceptRichText(False)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(10)
        self.source_edit.setFont(mono)
        self.source_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.tabs.addTab(self.source_edit, "HTML")

        # Pestaña vista previa
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.tabs.addTab(self.preview, "Vista previa")

        layout.addWidget(self.tabs)

        # Conexiones toolbar
        self.btn_bold.clicked.connect(lambda: self._wrap("<strong>", "</strong>"))
        self.btn_italic.clicked.connect(lambda: self._wrap("<em>", "</em>"))
        self.btn_p.clicked.connect(lambda: self._wrap("<p>", "</p>"))
        self.btn_h2.clicked.connect(lambda: self._wrap("<h2>", "</h2>"))
        self.btn_h3.clicked.connect(lambda: self._wrap("<h3>", "</h3>"))
        self.btn_ul.clicked.connect(self._insert_ul)
        self.btn_ol.clicked.connect(self._insert_ol)
        self.btn_hr.clicked.connect(lambda: self._insert_text("<hr>\n"))
        self.btn_link.clicked.connect(self._insert_link)

        self.tabs.currentChanged.connect(self._on_tab_change)

    # ------------------------------------------------------------------
    # Helpers de inserción
    # ------------------------------------------------------------------

    def _wrap(self, open_tag, close_tag):
        cursor = self.source_edit.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"{open_tag}{selected}{close_tag}")
        else:
            pos_before = cursor.position()
            cursor.insertText(f"{open_tag}{close_tag}")
            cursor.setPosition(pos_before + len(open_tag))
            self.source_edit.setTextCursor(cursor)
        self.source_edit.setFocus()

    def _insert_text(self, text):
        self.source_edit.textCursor().insertText(text)
        self.source_edit.setFocus()

    def _insert_ul(self):
        cursor = self.source_edit.textCursor()
        selected = cursor.selectedText()
        items = "\n".join(f"    <li>{line}</li>" for line in selected.splitlines()) \
                if selected else "    <li></li>"
        cursor.insertText(f"<ul>\n{items}\n</ul>\n")
        self.source_edit.setFocus()

    def _insert_ol(self):
        cursor = self.source_edit.textCursor()
        selected = cursor.selectedText()
        items = "\n".join(f"    <li>{line}</li>" for line in selected.splitlines()) \
                if selected else "    <li></li>"
        cursor.insertText(f"<ol>\n{items}\n</ol>\n")
        self.source_edit.setFocus()

    def _insert_link(self):
        cursor = self.source_edit.textCursor()
        selected = cursor.selectedText()

        dlg = QDialog(self)
        dlg.setWindowTitle("Insertar enlace")
        dlg.setMinimumWidth(360)
        form = QFormLayout(dlg)

        url_edit = QLineEdit()
        url_edit.setPlaceholderText("https://...")
        text_edit = QLineEdit()
        text_edit.setText(selected)
        text_edit.setPlaceholderText("Texto del enlace")

        form.addRow("URL:", url_edit)
        form.addRow("Texto:", text_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            url = url_edit.text().strip()
            text = text_edit.text().strip() or url
            if url:
                cursor.insertText(f'<a href="{url}">{text}</a>')
        self.source_edit.setFocus()

    def _on_tab_change(self, index):
        if index == 1:
            self.preview.setHtml(self.source_edit.toPlainText())

    # ------------------------------------------------------------------
    # API pública compatible con QTextEdit
    # ------------------------------------------------------------------

    def toPlainText(self):
        """Devuelve el HTML fuente (compatible con QTextEdit.toPlainText)."""
        return self.source_edit.toPlainText()

    def setPlainText(self, html):
        """Establece el HTML fuente (compatible con QTextEdit.setPlainText)."""
        self.source_edit.setPlainText(html or "")

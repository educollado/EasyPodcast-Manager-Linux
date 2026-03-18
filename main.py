#!/usr/bin/env python3
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import config
from ui.main_window import MainWindow
from ui.setup_dialog import SetupDialog


STYLESHEET = """
/* ── Paleta EasyPodcast ───────────────────────────────────────────── */
/* fondo: #f6f2eb  texto: #1c1814  acento: #8c3509  borde: #e5dfd4   */

QWidget {
    background-color: #f6f2eb;
    color: #1c1814;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}

/* Ventana principal y diálogos */
QMainWindow, QDialog {
    background-color: #f6f2eb;
}

/* Barra de menú */
QMenuBar {
    background-color: #e5dfd4;
    color: #1c1814;
    padding: 2px 4px;
    border-bottom: 1px solid #d4cec3;
}
QMenuBar::item:selected {
    background-color: #fff3ec;
    color: #8c3509;
    border-radius: 4px;
}
QMenu {
    background-color: #fdf9f5;
    border: 1px solid #e5dfd4;
}
QMenu::item:selected {
    background-color: #fff3ec;
    color: #8c3509;
}

/* Pestañas */
QTabWidget::pane {
    border: 1px solid #e5dfd4;
    border-radius: 6px;
    background-color: #fdf9f5;
    top: -1px;
}
QTabBar::tab {
    background-color: #e5dfd4;
    color: #5f544d;
    padding: 7px 18px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #d4cec3;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #fdf9f5;
    color: #8c3509;
    font-weight: bold;
    border-color: #e5dfd4;
}
QTabBar::tab:hover:!selected {
    background-color: #f0ebe2;
}

/* Botones */
QPushButton {
    background-color: #8c3509;
    color: #fff;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #a33f0a;
}
QPushButton:pressed {
    background-color: #6e2907;
}
QPushButton:disabled {
    background-color: #c9bfb5;
    color: #7a6f68;
}

/* Campos de texto */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #fff;
    border: 1px solid #e5dfd4;
    border-radius: 5px;
    padding: 5px 8px;
    color: #1c1814;
    selection-background-color: #fff3ec;
    selection-color: #8c3509;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #8c3509;
}

/* ComboBox */
QComboBox {
    background-color: #fff;
    border: 1px solid #e5dfd4;
    border-radius: 5px;
    padding: 5px 8px;
    color: #1c1814;
}
QComboBox:focus {
    border-color: #8c3509;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #fdf9f5;
    border: 1px solid #e5dfd4;
    selection-background-color: #fff3ec;
    selection-color: #8c3509;
}

/* Tabla */
QTableWidget {
    background-color: #fff;
    border: 1px solid #e5dfd4;
    border-radius: 5px;
    gridline-color: #f0ebe2;
    alternate-background-color: #fdf9f5;
}
QTableWidget::item:selected {
    background-color: #fff3ec;
    color: #8c3509;
}
QHeaderView::section {
    background-color: #e5dfd4;
    color: #1c1814;
    padding: 6px 10px;
    border: none;
    border-right: 1px solid #d4cec3;
    font-weight: 600;
}

/* Barra de estado */
QStatusBar {
    background-color: #e5dfd4;
    color: #5f544d;
    font-size: 12px;
    border-top: 1px solid #d4cec3;
}

/* ScrollBar */
QScrollBar:vertical {
    background: #f0ebe2;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #c9bfb5;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #8c3509;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* Etiquetas */
QLabel {
    color: #5f544d;
}

/* Separadores en formularios */
QFormLayout QLabel {
    font-weight: 500;
    color: #1c1814;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("EasyPodcast Manager")
    app.setOrganizationName("EasyPodcast")
    app.setStyleSheet(STYLESHEET)
    icon_path = os.path.join(os.path.dirname(__file__), "easypodcast.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()

    if not config.has_config():
        dlg = SetupDialog(window)
        if dlg.exec() != SetupDialog.DialogCode.Accepted:
            sys.exit(0)
        window._load_api()
        window._build_tabs()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

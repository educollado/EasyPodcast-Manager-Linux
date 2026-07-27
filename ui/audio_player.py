from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt, QUrl, QSize, QPoint, QRect
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPolygon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


def _icon_play(size=20):
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#1c1814"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygon([QPoint(4, 2), QPoint(4, size - 2), QPoint(size - 2, size // 2)]))
    p.end()
    return QIcon(px)


def _icon_pause(size=20):
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#1c1814"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRect(3, 2, 5, size - 4), 1, 1)
    p.drawRoundedRect(QRect(12, 2, 5, size - 4), 1, 1)
    p.end()
    return QIcon(px)


def _icon_stop(size=20):
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#1c1814"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRect(3, 3, size - 6, size - 6), 2, 2)
    p.end()
    return QIcon(px)


BTN_STYLE = (
    "QPushButton { background-color: #fff3ec; border: 1px solid #e5dfd4; border-radius: 5px; }"
    "QPushButton:hover { background-color: #ffe8d6; border-color: #8c3509; }"
    "QPushButton:pressed { background-color: #ffd5b8; }"
)


class AudioPlayerField(QWidget):
    """QLineEdit con reproductor de audio compacto al lado."""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)

        self._ico_play = _icon_play()
        self._ico_pause = _icon_pause()
        self._ico_stop = _icon_stop()

        # Qt conecta con PipeWire/PulseAudio al crear QAudioOutput. Se inicializa
        # al pulsar reproducir para que abrir un formulario nunca dependa del
        # estado del subsistema de audio.
        self._player = None
        self._audio_out = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        layout.addWidget(self.line_edit)

        self.btn_play = QPushButton()
        self.btn_play.setIcon(self._ico_play)
        self.btn_play.setIconSize(QSize(20, 20))
        self.btn_play.setFixedSize(38, 38)
        self.btn_play.setToolTip("Reproducir / Pausar")
        self.btn_play.setStyleSheet(BTN_STYLE)
        self.btn_play.clicked.connect(self._on_play_pause)
        layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(self._ico_stop)
        self.btn_stop.setIconSize(QSize(20, 20))
        self.btn_stop.setFixedSize(38, 38)
        self.btn_stop.setToolTip("Detener")
        self.btn_stop.setStyleSheet(BTN_STYLE)
        self.btn_stop.clicked.connect(self._on_stop)
        layout.addWidget(self.btn_stop)

        self.status_label = QLabel("")
        self.status_label.setFixedWidth(50)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setStyleSheet("color: #7a6f68; font-size: 11px;")
        layout.addWidget(self.status_label)

    # --- API pública compatible con QLineEdit ---

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text or "")
        if self._player is not None:
            self._player.stop()

    def setPlaceholderText(self, text):
        self.line_edit.setPlaceholderText(text)

    # --- Controles ---

    def _ensure_player(self):
        if self._player is not None:
            return
        self._player = QMediaPlayer(self)
        self._audio_out = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_out)
        self._audio_out.setVolume(1.0)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.errorOccurred.connect(self._on_error)

    def _on_play_pause(self):
        url = self.line_edit.text().strip()
        if not url:
            return
        self._ensure_player()
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._player.play()
        else:
            self._player.setSource(QUrl(url))
            self._player.play()

    def _on_stop(self):
        if self._player is not None:
            self._player.stop()

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setIcon(self._ico_pause)
            self.status_label.setText("play")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.btn_play.setIcon(self._ico_play)
            self.status_label.setText("pausa")
        else:
            self.btn_play.setIcon(self._ico_play)
            self.status_label.setText("")

    def _on_error(self, error, msg):
        self.status_label.setText("error")
        self.status_label.setToolTip(msg)

import os
import wave
import tempfile
import numpy as np
import sounddevice as sd

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialogButtonBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QPalette


class _RecordThread(QThread):
    finished = Signal(str)   # ruta al MP3 resultante
    error = Signal(str)

    SAMPLE_RATE = 44100

    def __init__(self):
        super().__init__()
        self._chunks = []
        self._running = False

    def run(self):
        self._chunks = []
        self._running = True
        try:
            with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=1,
                                dtype="float32", callback=self._callback):
                while self._running:
                    self.msleep(50)
        except Exception as e:
            self.error.emit(str(e))
            return

        if not self._chunks:
            self.error.emit("No se capturó audio.")
            return

        audio = np.concatenate(self._chunks, axis=0)
        tmp_wav = tempfile.mktemp(suffix=".wav")
        self._save_wav(tmp_wav, audio)

        tmp_mp3 = tempfile.mktemp(suffix=".mp3")
        try:
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_wav, "-codec:a", "libmp3lame", "-b:a", "128k", tmp_mp3],
                capture_output=True
            )
            os.unlink(tmp_wav)
            if result.returncode == 0:
                self.finished.emit(tmp_mp3)
            else:
                self.error.emit(result.stderr.decode(errors="replace")[-200:])
        except Exception as e:
            self.error.emit(str(e))

    def _callback(self, indata, frames, time_info, status):
        self._chunks.append(indata.copy())

    def _save_wav(self, path, audio):
        audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.SAMPLE_RATE)
            f.writeframes(audio_int16.tobytes())

    def stop(self):
        self._running = False


class RecorderDialog(QDialog):
    """Diálogo de grabación. Devuelve la ruta al MP3 si el usuario acepta."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Grabar audio")
        self.setFixedSize(320, 220)
        self._thread = None
        self._mp3_path = None
        self._seconds = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.status_label = QLabel("Listo para grabar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 28px; color: #8c3509;")
        layout.addWidget(self.time_label)

        btn_row = QHBoxLayout()

        self.btn_record = QPushButton("⏺  Grabar")
        self.btn_record.setMinimumHeight(40)
        self.btn_record.clicked.connect(self._on_record)
        btn_row.addWidget(self.btn_record)

        self.btn_stop = QPushButton("⏹  Detener")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        btn_row.addWidget(self.btn_stop)

        layout.addLayout(btn_row)
        layout.addSpacing(16)

        self.btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self._on_cancel)
        layout.addWidget(self.btn_box)

    def _on_record(self):
        self._seconds = 0
        self.time_label.setText("00:00")
        self.status_label.setText("Grabando...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0392b;")
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self._thread = _RecordThread()
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()
        self._timer.start(1000)

    def _on_stop(self):
        self._timer.stop()
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Procesando...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #5f544d;")
        if self._thread:
            self._thread.stop()

    def _tick(self):
        self._seconds += 1
        m, s = divmod(self._seconds, 60)
        self.time_label.setText(f"{m:02d}:{s:02d}")

    def _on_finished(self, path):
        self._mp3_path = path
        fname = os.path.basename(path)
        self.status_label.setText(f"Listo: {fname}")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        self.btn_record.setEnabled(True)
        self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def _on_error(self, msg):
        self._timer.stop()
        self.status_label.setText(f"Error: {msg}")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0392b;")
        self.btn_record.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _on_cancel(self):
        if self._thread and self._thread.isRunning():
            self._thread.stop()
            self._thread.wait()
        self.reject()

    def get_path(self):
        return self._mp3_path

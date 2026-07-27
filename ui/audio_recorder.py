import os
import wave
import tempfile
import numpy as np

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialogButtonBox,
    QWidget, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QPainter


# Nombres de dispositivos ALSA virtuales que no son micrófonos reales
_SKIP_DEVICES = {
    "lavrate", "samplerate", "speexrate", "speex", "upmix", "vdownmix",
    "oss", "dmix", "front", "surround40", "iec958", "spdif", "/dev/dsp",
}


def _list_input_devices():
    """Devuelve lista de (device_index, label) con dispositivos de entrada útiles."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
    except Exception:
        return []

    result = []
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0 and d["name"].strip() not in _SKIP_DEVICES:
            result.append((i, d["name"]))
    return result


def _preferred_device(devices):
    """Devuelve el índice en la lista 'devices' del dispositivo más adecuado.
    Prioriza hardware real (hw:) sobre pulse/default."""
    for idx, (_, name) in enumerate(devices):
        if "hw:" in name:
            return idx
    return 0


class VuMeter(QWidget):
    """Medidor de nivel de audio estilo LED segmentado con suavizado."""

    _SEGMENTS = 20
    _ATTACK = 0.6    # qué rápido sube  (1.0 = instantáneo)
    _DECAY  = 0.12   # qué rápido baja  (valor pequeño = caída lenta)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target = 0.0     # nivel recibido del hilo
        self._displayed = 0.0  # nivel suavizado que se pinta
        self.setFixedHeight(14)

        self._anim = QTimer(self)
        self._anim.setInterval(40)   # ~25 fps
        self._anim.timeout.connect(self._animate)
        self._anim.start()

    def set_level(self, level: float):
        self._target = max(0.0, min(1.0, level))

    def _animate(self):
        if self._target > self._displayed:
            self._displayed += (self._target - self._displayed) * self._ATTACK
        else:
            self._displayed += (self._target - self._displayed) * self._DECAY
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        n = self._SEGMENTS
        gap = 2
        seg_w = (w - gap * (n - 1)) / n
        active = int(self._displayed * n)

        for i in range(n):
            x = int(i * (seg_w + gap))
            sw = max(1, int(seg_w))
            if i < active:
                if i < int(n * 0.60):
                    color = QColor("#2ecc71")   # verde
                elif i < int(n * 0.85):
                    color = QColor("#f39c12")   # naranja
                else:
                    color = QColor("#e74c3c")   # rojo
            else:
                color = QColor("#e5dfd4")       # inactivo
            painter.fillRect(x, 0, sw, h, color)


class _RecordThread(QThread):
    finished = Signal(str)   # ruta al MP3 resultante
    error = Signal(str)
    level = Signal(float)    # 0.0 – 1.0, RMS del chunk

    SAMPLE_RATE = 44100

    def __init__(self, device=None):
        super().__init__()
        self._chunks = []
        self._running = False
        self._device = device

    def run(self):
        self._chunks = []
        self._running = True
        try:
            import sounddevice as sd
            with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=1,
                                dtype="float32", device=self._device,
                                callback=self._callback):
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
        rms = float(np.sqrt(np.mean(indata ** 2)))
        self.level.emit(min(rms * 8, 1.0))

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
        self.setFixedSize(380, 290)
        self._thread = None
        self._mp3_path = None
        self._seconds = 0
        self._input_devices = _list_input_devices()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Selector de dispositivo ---
        dev_row = QHBoxLayout()
        dev_lbl = QLabel("Micrófono:")
        dev_lbl.setStyleSheet("font-size: 11px; color: #5f544d;")
        dev_lbl.setFixedWidth(68)
        dev_row.addWidget(dev_lbl)
        self._dev_combo = QComboBox()
        self._dev_combo.setStyleSheet("font-size: 11px;")
        for _, name in self._input_devices:
            self._dev_combo.addItem(name)
        if self._input_devices:
            self._dev_combo.setCurrentIndex(_preferred_device(self._input_devices))
        dev_row.addWidget(self._dev_combo, 1)
        layout.addLayout(dev_row)

        self.status_label = QLabel("Listo para grabar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 28px; color: #8c3509;")
        layout.addWidget(self.time_label)

        # --- VU meter ---
        meter_row = QHBoxLayout()
        meter_lbl = QLabel("Nivel:")
        meter_lbl.setStyleSheet("font-size: 11px; color: #5f544d;")
        meter_lbl.setFixedWidth(36)
        meter_row.addWidget(meter_lbl)
        self._vu = VuMeter()
        meter_row.addWidget(self._vu, 1)
        layout.addLayout(meter_row)

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

        layout.addSpacing(4)

        self.btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.btn_box.accepted.connect(self.accept)
        self.btn_box.rejected.connect(self._on_cancel)
        layout.addWidget(self.btn_box)

    def _selected_device(self):
        idx = self._dev_combo.currentIndex()
        if 0 <= idx < len(self._input_devices):
            return self._input_devices[idx][0]  # device index para sounddevice
        return None

    def _on_record(self):
        self._seconds = 0
        self.time_label.setText("00:00")
        self.status_label.setText("Grabando...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0392b;")
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._dev_combo.setEnabled(False)
        self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self._thread = _RecordThread(device=self._selected_device())
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.level.connect(self._vu.set_level)
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
        self._vu.set_level(0.0)
        self._dev_combo.setEnabled(True)
        fname = os.path.basename(path)
        self.status_label.setText(f"Listo: {fname}")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        self.btn_record.setEnabled(True)
        self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def _on_error(self, msg):
        self._timer.stop()
        self._vu.set_level(0.0)
        self._dev_combo.setEnabled(True)
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

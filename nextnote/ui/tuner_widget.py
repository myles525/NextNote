"""Top-half tuner: big note-name label + gauge + status line."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from nextnote.config import IN_TUNE_CENTS_THRESHOLD, MIN_NOTE_RMS
from nextnote.theory.notes import freq_to_note_and_cents
from nextnote.ui.gauge_widget import GaugeWidget


class TunerWidget(QWidget):
    """Top-half tuner display: current note name, the gauge dial, and a
    status line. Driven entirely by slots connected to AnalysisWorker's
    signals — never touches audio/DSP state directly."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.note_label = QLabel("--")
        self.note_label.setAlignment(Qt.AlignCenter)
        self.note_label.setStyleSheet("font-size: 56px; font-weight: bold; color: #999;")

        self.gauge = GaugeWidget()

        self.status_label = QLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; font-size: 13px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.note_label)
        layout.addWidget(self.gauge)
        layout.addWidget(self.status_label)

    def on_pitch_updated(self, freq_hz: float, rms: float) -> None:
        """Slot for AnalysisWorker.pitch_updated. Shows an idle state when
        the signal is too quiet/absent, otherwise updates the note label and
        gauge with color feedback based on the in-tune threshold."""
        if rms < MIN_NOTE_RMS or freq_hz <= 0:
            self.note_label.setText("--")
            self.note_label.setStyleSheet("font-size: 56px; font-weight: bold; color: #999;")
            self.gauge.set_idle()
            return

        name, _midi, cents = freq_to_note_and_cents(freq_hz)
        in_tune = abs(cents) <= IN_TUNE_CENTS_THRESHOLD
        color = "#3cc85a" if in_tune else "#d23c3c"
        self.note_label.setText(name)
        self.note_label.setStyleSheet(f"font-size: 56px; font-weight: bold; color: {color};")
        self.gauge.set_cents(cents, in_tune)

    def on_status_changed(self, status: str) -> None:
        """Slot for AnalysisWorker.status_changed; shows status/error text."""
        self.status_label.setText(status)

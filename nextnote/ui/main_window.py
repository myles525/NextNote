"""Top-level window: tuner on top, note log + key/recommendation panel on bottom."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QSplitter, QWidget

from nextnote.audio.worker import AnalysisWorker
from nextnote.config import RECENCY_DECAY_NOTES
from nextnote.theory.key_detection import KeyDetector
from nextnote.theory.recommend import recommend_next_notes
from nextnote.ui.key_panel import KeyPanel
from nextnote.ui.sequence_widget import SequenceWidget
from nextnote.ui.tuner_widget import TunerWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NextNote")

        self.tuner_widget = TunerWidget()
        self.sequence_widget = SequenceWidget()
        self.key_panel = KeyPanel()

        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.addWidget(self.sequence_widget, stretch=1)
        bottom_layout.addWidget(self.key_panel, stretch=1)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tuner_widget)
        splitter.addWidget(bottom_container)
        splitter.setSizes([350, 350])
        self.setCentralWidget(splitter)

        self.key_detector = KeyDetector()
        self.worker = AnalysisWorker()
        self._wire_signals()
        self.worker.start()

    def _wire_signals(self) -> None:
        self.worker.pitch_updated.connect(self.tuner_widget.on_pitch_updated)
        self.worker.status_changed.connect(self.tuner_widget.on_status_changed)
        self.worker.note_confirmed.connect(self._on_note_confirmed)

    def _on_note_confirmed(self, note_name: str, midi_number: int, timestamp_sec: float) -> None:
        self.sequence_widget.on_note_confirmed(note_name, midi_number)
        self.key_detector.add_note(midi_number, timestamp_sec)

        key_result = self.key_detector.detect()
        if key_result is not None:
            self.key_panel.on_key_updated(key_result.name, key_result.correlation)
            recent_pcs = self.sequence_widget.recent_pitch_classes(RECENCY_DECAY_NOTES)
            recs = recommend_next_notes(key_result, recent_pcs)
            self.key_panel.on_recommendation_updated(recs)

    def closeEvent(self, event) -> None:
        self.worker.stop()
        super().closeEvent(event)

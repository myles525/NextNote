"""Top-level window: tuner on top, note log + scale panel on bottom."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QSplitter, QWidget

from nextnote.audio.worker import AnalysisWorker
from nextnote.config import RECENCY_DECAY_NOTES
from nextnote.theory.notes import NOTE_NAMES, pitch_class
from nextnote.theory.recommend import recommend_next_notes
from nextnote.theory.scales import nearest_in_scale_note, scale_pitch_classes
from nextnote.ui.scale_panel import ScalePanel
from nextnote.ui.sequence_widget import SequenceWidget
from nextnote.ui.tuner_widget import TunerWidget


class MainWindow(QMainWindow):
    """Top-level application window: tuner on top, note log + scale panel on
    bottom. Owns the audio worker thread and the currently selected scale,
    and is the only place that wires audio-side signals to UI-side widgets."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NextNote")

        self.tuner_widget = TunerWidget()
        self.sequence_widget = SequenceWidget()
        self.scale_panel = ScalePanel()

        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.addWidget(self.sequence_widget, stretch=1)
        bottom_layout.addWidget(self.scale_panel, stretch=1)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tuner_widget)
        splitter.addWidget(bottom_container)
        splitter.setSizes([350, 350])
        self.setCentralWidget(splitter)

        root_pc, scale_type = self.scale_panel.selector.current_selection()
        self._scale_pcs = scale_pitch_classes(root_pc, scale_type)
        self._refresh_scale_display()

        self.worker = AnalysisWorker()
        self._wire_signals()
        self.worker.start()

    def _wire_signals(self) -> None:
        """Connect AnalysisWorker's Qt signals to the widgets/handlers that
        react to them. Qt marshals these calls onto the UI thread
        automatically since the worker lives on a different thread."""
        self.worker.pitch_updated.connect(self.tuner_widget.on_pitch_updated)
        self.worker.status_changed.connect(self.tuner_widget.on_status_changed)
        self.worker.note_confirmed.connect(self._on_note_confirmed)
        self.scale_panel.selector.scale_changed.connect(self._on_scale_changed)

    def _on_scale_changed(self, root_pc: int, scale_type: str) -> None:
        """Slot for ScaleSelectorWidget.scale_changed: updates which pitch
        classes count as 'in scale' and refreshes the notes/recommendations
        shown for it."""
        self._scale_pcs = scale_pitch_classes(root_pc, scale_type)
        self._refresh_scale_display()

    def _refresh_scale_display(self) -> None:
        """Update the scale-notes badges and recommendation row for
        self._scale_pcs, using whatever note history exists so far."""
        note_names = [NOTE_NAMES[pc] for pc in self._scale_pcs]
        self.scale_panel.set_scale_notes_display(note_names)

        recent_pcs = self.sequence_widget.recent_pitch_classes(RECENCY_DECAY_NOTES)
        recs = recommend_next_notes(self._scale_pcs, recent_pcs)
        self.scale_panel.set_recommendations(recs)

    def _on_note_confirmed(self, note_name: str, midi_number: int, timestamp_sec: float) -> None:
        """Slot for AnalysisWorker.note_confirmed. Logs the note (color-coded
        by scale membership), shows a nearest-note suggestion if it fell
        outside the selected scale, and refreshes what to play next."""
        in_scale = pitch_class(midi_number) in self._scale_pcs
        self.sequence_widget.on_note_confirmed(note_name, midi_number, in_scale)

        if in_scale:
            self.scale_panel.show_in_scale(note_name)
        else:
            suggestion_name, _suggestion_midi = nearest_in_scale_note(midi_number, self._scale_pcs)
            self.scale_panel.show_out_of_scale(note_name, suggestion_name)

        recent_pcs = self.sequence_widget.recent_pitch_classes(RECENCY_DECAY_NOTES)
        recs = recommend_next_notes(self._scale_pcs, recent_pcs)
        self.scale_panel.set_recommendations(recs)

    def closeEvent(self, event) -> None:
        """Ensure the audio worker thread and its input stream are stopped
        cleanly before the window (and process) closes."""
        self.worker.stop()
        super().closeEvent(event)

"""Bottom-left: scrolling log of confirmed notes played."""

from PyQt5.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from nextnote.config import SEQUENCE_LOG_MAX_ITEMS
from nextnote.theory.notes import pitch_class


class SequenceWidget(QWidget):
    """Bottom-left panel: a scrolling log of confirmed notes, and the
    underlying MIDI history used to feed key detection and recommendations."""

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QLabel("Notes Played")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.note_list = QListWidget()
        self._midi_history: list[int] = []

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.note_list)

    def on_note_confirmed(self, note_name: str, midi_number: int) -> None:
        """Slot for AnalysisWorker.note_confirmed: appends the note to the
        visible log and its MIDI history, trimming both to the configured
        maximum length."""
        self.note_list.addItem(note_name)
        self.note_list.scrollToBottom()
        self._midi_history.append(midi_number)

        while self.note_list.count() > SEQUENCE_LOG_MAX_ITEMS:
            self.note_list.takeItem(0)
        if len(self._midi_history) > SEQUENCE_LOG_MAX_ITEMS:
            self._midi_history = self._midi_history[-SEQUENCE_LOG_MAX_ITEMS:]

    def recent_pitch_classes(self, n: int) -> list[int]:
        """Pitch classes (0-11) of the last n notes played, oldest first —
        used by MainWindow to feed the recommendation logic."""
        return [pitch_class(m) for m in self._midi_history[-n:]]

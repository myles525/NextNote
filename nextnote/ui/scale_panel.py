"""Bottom-right panel: scale picker, the notes it contains, and feedback on
whether the last note played was in that scale."""

from __future__ import annotations

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from nextnote.ui.scale_selector import ScaleSelectorWidget

IN_SCALE_STYLE = "font-weight: bold; font-size: 18px; margin-top: 12px; color: #3cc85a;"
OUT_OF_SCALE_STYLE = "font-weight: bold; font-size: 18px; margin-top: 12px; color: #d23c3c;"
IDLE_STYLE = "font-weight: bold; font-size: 18px; margin-top: 12px; color: #888;"


class ScalePanel(QWidget):
    """Hosts the ScaleSelectorWidget plus a display of the current scale's
    notes and a feedback line reacting to each confirmed note."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selector = ScaleSelectorWidget()

        self.scale_notes_label = QLabel("")
        self.scale_notes_label.setStyleSheet("color: #555; font-size: 13px; margin-top: 8px;")

        self.feedback_label = QLabel("Play a note to get started")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setStyleSheet(IDLE_STYLE)

        layout = QVBoxLayout(self)
        layout.addWidget(self.selector)
        layout.addWidget(self.scale_notes_label)
        layout.addWidget(self.feedback_label)
        layout.addStretch()

    def set_scale_notes_display(self, note_names: list[str]) -> None:
        """Show the notes that make up the currently selected scale."""
        self.scale_notes_label.setText("Notes: " + ", ".join(note_names))

    def show_in_scale(self, note_name: str) -> None:
        """Positive feedback for a note that belongs to the current scale."""
        self.feedback_label.setText(f"✓ {note_name} — in scale")
        self.feedback_label.setStyleSheet(IN_SCALE_STYLE)

    def show_out_of_scale(self, note_name: str, suggestion_name: str) -> None:
        """Feedback for a note outside the current scale, naming the nearest
        note (by semitone distance) that would have been in it."""
        self.feedback_label.setText(f"✗ {note_name} is outside the scale — try {suggestion_name}")
        self.feedback_label.setStyleSheet(OUT_OF_SCALE_STYLE)

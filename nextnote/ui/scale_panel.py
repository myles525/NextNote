"""Bottom-right panel: scale picker, the scale's notes, feedback on the last
note played, and ranked suggestions for what to play next."""

from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nextnote.ui.scale_selector import ScaleSelectorWidget

IN_SCALE_STYLE = "font-weight: bold; font-size: 18px; margin-top: 12px; color: #3cc85a;"
OUT_OF_SCALE_STYLE = "font-weight: bold; font-size: 18px; margin-top: 12px; color: #d23c3c;"
IDLE_STYLE = "font-weight: bold; font-size: 18px; margin-top: 12px; color: #888;"

SCALE_NOTE_BADGE_STYLE = (
    "background-color: #e4e4e4; color: #333; border-radius: 10px;"
    "padding: 4px 12px; font-weight: bold; font-size: 14px;"
)
RECOMMEND_BADGE_STYLE = (
    "background-color: #4a7fd6; color: white; border-radius: 10px;"
    "padding: 6px 14px; font-weight: bold; font-size: 15px;"
)


class ScalePanel(QWidget):
    """Hosts the ScaleSelectorWidget plus a badge display of the current
    scale's notes, a feedback line reacting to each confirmed note, and a
    ranked "try playing next" recommendation row."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selector = ScaleSelectorWidget()

        scale_notes_title = QLabel("Scale Notes")
        scale_notes_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 8px;")
        self.scale_notes_row = QHBoxLayout()
        self._scale_note_badges: list[QLabel] = []

        self.feedback_label = QLabel("Play a note to get started")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setStyleSheet(IDLE_STYLE)

        recommend_title = QLabel("Try Playing Next")
        recommend_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 12px;")
        self.recommend_row = QHBoxLayout()
        self._recommend_badges: list[QLabel] = []

        layout = QVBoxLayout(self)
        layout.addWidget(self.selector)
        layout.addWidget(scale_notes_title)
        layout.addLayout(self.scale_notes_row)
        layout.addWidget(self.feedback_label)
        layout.addWidget(recommend_title)
        layout.addLayout(self.recommend_row)
        layout.addStretch()

    def set_scale_notes_display(self, note_names: list[str]) -> None:
        """Show the notes that make up the currently selected scale, root first."""
        self._set_badges(self.scale_notes_row, self._scale_note_badges, note_names, SCALE_NOTE_BADGE_STYLE)

    def set_recommendations(self, note_names: list[str]) -> None:
        """Show the ranked "try playing next" suggestions, best first."""
        self._set_badges(self.recommend_row, self._recommend_badges, note_names, RECOMMEND_BADGE_STYLE)

    def show_in_scale(self, note_name: str) -> None:
        """Positive feedback for a note that belongs to the current scale."""
        self.feedback_label.setText(f"✓ {note_name} — in scale")
        self.feedback_label.setStyleSheet(IN_SCALE_STYLE)

    def show_out_of_scale(self, note_name: str, suggestion_name: str) -> None:
        """Feedback for a note outside the current scale, naming the nearest
        note (by semitone distance) that would have been in it."""
        self.feedback_label.setText(f"✗ {note_name} is outside the scale — try {suggestion_name}")
        self.feedback_label.setStyleSheet(OUT_OF_SCALE_STYLE)

    @staticmethod
    def _set_badges(row: QHBoxLayout, tracked: list[QLabel], names: list[str], style: str) -> None:
        """Replace the badge widgets in a row with one per given name."""
        for badge in tracked:
            row.removeWidget(badge)
            badge.deleteLater()
        tracked.clear()

        for name in names:
            badge = QLabel(name)
            badge.setStyleSheet(style)
            row.addWidget(badge)
            tracked.append(badge)

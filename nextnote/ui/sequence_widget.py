"""Bottom-left: scrolling log of confirmed notes played, color-coded by
whether each note was in the currently selected scale."""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from nextnote.config import SEQUENCE_LOG_MAX_ITEMS

IN_SCALE_COLOR = QColor(60, 200, 90)
OUT_OF_SCALE_COLOR = QColor(210, 60, 60)


class SequenceWidget(QWidget):
    """Bottom-left panel: a scrolling, color-coded log of confirmed notes."""

    def __init__(self, parent=None):
        super().__init__(parent)

        title = QLabel("Notes Played")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.note_list = QListWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.note_list)

    def on_note_confirmed(self, note_name: str, in_scale: bool) -> None:
        """Append the note to the log, colored green if it's in the current
        scale or red if not, trimming the log to its configured max length."""
        item = QListWidgetItem(note_name)
        item.setForeground(IN_SCALE_COLOR if in_scale else OUT_OF_SCALE_COLOR)
        self.note_list.addItem(item)
        self.note_list.scrollToBottom()

        while self.note_list.count() > SEQUENCE_LOG_MAX_ITEMS:
            self.note_list.takeItem(0)

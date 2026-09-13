"""Lets the player manually pick a root note and scale type to practice in."""

from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from nextnote.theory.notes import NOTE_NAMES
from nextnote.theory.scales import SCALE_DEFINITIONS


class ScaleSelectorWidget(QWidget):
    """Two dropdowns (root note, scale type) that together define the scale
    the rest of the app checks played notes against."""

    scale_changed = pyqtSignal(int, str)  # (root_pitch_class, scale_type)

    def __init__(self, parent=None):
        super().__init__(parent)

        label = QLabel("Scale:")
        label.setStyleSheet("font-weight: bold;")

        self.root_combo = QComboBox()
        self.root_combo.addItems(NOTE_NAMES)

        self.type_combo = QComboBox()
        self.type_combo.addItems(list(SCALE_DEFINITIONS.keys()))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addWidget(self.root_combo)
        layout.addWidget(self.type_combo)
        layout.addStretch()

        self.root_combo.currentIndexChanged.connect(self._emit_changed)
        self.type_combo.currentIndexChanged.connect(self._emit_changed)

    def _emit_changed(self) -> None:
        root_pc, scale_type = self.current_selection()
        self.scale_changed.emit(root_pc, scale_type)

    def current_selection(self) -> tuple[int, str]:
        """The currently selected (root_pitch_class, scale_type)."""
        return self.root_combo.currentIndex(), self.type_combo.currentText()

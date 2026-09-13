"""Bottom-right: detected key/scale label + recommended-note badges."""

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class KeyPanel(QWidget):
    """Bottom-right panel: shows the detected key/scale and a row of
    recommended-note badges, rebuilt each time the recommendation changes."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.key_label = QLabel("Key: --")
        self.key_label.setStyleSheet("font-weight: bold; font-size: 20px;")

        rec_title = QLabel("Try Playing Next")
        rec_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 12px;")

        self.badge_row = QHBoxLayout()

        layout = QVBoxLayout(self)
        layout.addWidget(self.key_label)
        layout.addWidget(rec_title)
        layout.addLayout(self.badge_row)
        layout.addStretch()

        self._badge_widgets: list[QLabel] = []

    def on_key_updated(self, key_name: str, confidence: float) -> None:
        """Update the key label; dims the text when correlation confidence
        is low, as a subtle hint the detection may not be reliable yet."""
        self.key_label.setText(f"Key: {key_name}")
        opacity = "color: #222;" if confidence > 0.5 else "color: #888;"
        self.key_label.setStyleSheet(f"font-weight: bold; font-size: 20px; {opacity}")

    def on_recommendation_updated(self, note_names: list[str]) -> None:
        """Replace the recommendation badges with one per given note name,
        best suggestion first."""
        for badge in self._badge_widgets:
            self.badge_row.removeWidget(badge)
            badge.deleteLater()
        self._badge_widgets.clear()

        for name in note_names:
            badge = QLabel(name)
            badge.setStyleSheet(
                "background-color: #4a7fd6; color: white; border-radius: 10px;"
                "padding: 6px 14px; font-weight: bold; font-size: 15px;"
            )
            self.badge_row.addWidget(badge)
            self._badge_widgets.append(badge)

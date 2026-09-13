"""Custom-painted semicircular needle gauge showing cents sharp/flat."""

import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from nextnote.config import CENTS_DISPLAY_RANGE, IN_TUNE_CENTS_THRESHOLD

IN_TUNE_COLOR = QColor(60, 200, 90)
OUT_OF_TUNE_COLOR = QColor(210, 60, 60)
NEUTRAL_COLOR = QColor(150, 150, 150)


class GaugeWidget(QWidget):
    """A semicircular needle dial showing how many cents sharp/flat the
    currently detected pitch is, with color feedback (green when in tune)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cents = 0.0
        self._in_tune = False
        self._active = False
        self.setMinimumSize(260, 160)

    def set_cents(self, cents: float, in_tune: bool) -> None:
        """Update the needle position. cents is clamped to the display
        range; in_tune controls the needle/arc color."""
        self._cents = max(-CENTS_DISPLAY_RANGE, min(CENTS_DISPLAY_RANGE, cents))
        self._in_tune = in_tune
        self._active = True
        self.update()

    def set_idle(self) -> None:
        """Show a neutral gray needle, e.g. when there's no signal to tune to."""
        self._active = False
        self.update()

    def paintEvent(self, event) -> None:
        """Qt paint callback: draws the background arc, in-tune (green) zone,
        tick marks every 10 cents, the needle, and a center indicator dot."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h * 0.9
        radius = min(w / 2.0, h) * 0.85

        arc_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # Background arc (amber), green zone overlaid within in-tune threshold.
        painter.setPen(QPen(QColor(220, 170, 60), 10, cap=Qt.FlatCap))
        painter.drawArc(arc_rect, 0 * 16, 180 * 16)

        green_span_deg = (IN_TUNE_CENTS_THRESHOLD / CENTS_DISPLAY_RANGE) * 90.0
        painter.setPen(QPen(IN_TUNE_COLOR, 10, cap=Qt.FlatCap))
        start_angle = int((90 - green_span_deg) * 16)
        span_angle = int((green_span_deg * 2) * 16)
        painter.drawArc(arc_rect, start_angle, span_angle)

        # Tick marks every 10 cents.
        painter.setPen(QPen(QColor(90, 90, 90), 2))
        for tick_cents in range(-50, 51, 10):
            angle_deg = 180.0 - ((tick_cents + CENTS_DISPLAY_RANGE) / (2 * CENTS_DISPLAY_RANGE)) * 180.0
            angle_rad = math.radians(angle_deg)
            inner = radius - 14
            x1 = cx + inner * math.cos(angle_rad)
            y1 = cy - inner * math.sin(angle_rad)
            x2 = cx + radius * math.cos(angle_rad)
            y2 = cy - radius * math.sin(angle_rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Needle.
        if self._active:
            needle_color = IN_TUNE_COLOR if self._in_tune else OUT_OF_TUNE_COLOR
        else:
            needle_color = NEUTRAL_COLOR
        needle_angle_deg = 180.0 - ((self._cents + CENTS_DISPLAY_RANGE) / (2 * CENTS_DISPLAY_RANGE)) * 180.0
        needle_rad = math.radians(needle_angle_deg)
        needle_len = radius - 6
        tip_x = cx + needle_len * math.cos(needle_rad)
        tip_y = cy - needle_len * math.sin(needle_rad)
        painter.setPen(QPen(needle_color, 4, cap=Qt.RoundCap))
        painter.drawLine(QPointF(cx, cy), QPointF(tip_x, tip_y))

        # Center indicator dot.
        painter.setBrush(needle_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 7, 7)

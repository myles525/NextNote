"""Simplified Krumhansl-Schmuckler-style key detection.

Builds a 12-bin pitch-class histogram of recently played notes and correlates
it against 24 rotated templates (major/natural-minor x 12 roots), picking the
best-correlating one.

Note: natural minor and its relative major share identical pitch classes, so
pitch-content-only detection cannot distinguish e.g. A minor from C major.
This is an expected, documented limitation rather than a bug.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from nextnote.config import (
    KEY_MIN_NOTES_TO_ANALYZE,
    KEY_WINDOW_MAX_AGE_SEC,
    KEY_WINDOW_NOTE_COUNT,
)
from nextnote.theory.notes import NOTE_NAMES

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Hand-set weights emphasizing tonic/dominant/mediant, in the spirit of the
# classic Krumhansl-Schmuckler perceptual profiles but simplified.
MAJOR_WEIGHTS = np.array([6, 0, 3, 0, 4, 3, 0, 5, 0, 3, 0, 2], dtype=float)
MINOR_WEIGHTS = np.array([6, 0, 3, 4, 0, 3, 0, 5, 3, 0, 2, 0], dtype=float)


@dataclass
class KeyResult:
    """The best-matching key/scale for a window of recently played notes.

    Attributes:
        root_pitch_class: 0-11 (0=C, 1=C#, ... 11=B) tonic of the detected key.
        is_major: True for major, False for natural minor.
        correlation: Pearson correlation of the observed pitch-class histogram
            against this key's template; higher means a more confident match.
        scale_notes: the 7 pitch classes (0-11) that make up the scale,
            starting with the root.
    """

    root_pitch_class: int
    is_major: bool
    correlation: float
    scale_notes: list[int]

    @property
    def name(self) -> str:
        """Human-readable key name, e.g. 'A Minor'."""
        mode = "Major" if self.is_major else "Minor"
        return f"{NOTE_NAMES[self.root_pitch_class]} {mode}"


class KeyDetector:
    """Tracks a sliding window of recently played notes and estimates the
    most likely key/scale from their pitch-class distribution."""

    def __init__(
        self,
        window_note_count: int = KEY_WINDOW_NOTE_COUNT,
        window_max_age_sec: float = KEY_WINDOW_MAX_AGE_SEC,
        min_notes: int = KEY_MIN_NOTES_TO_ANALYZE,
    ):
        """
        Args:
            window_note_count: keep at most this many of the most recent notes.
            window_max_age_sec: also drop notes older than this many seconds,
                so the detected key can follow the player as they change keys.
            min_notes: don't attempt detection until at least this many notes
                have been played (too few notes give unreliable correlations).
        """
        self._window_note_count = window_note_count
        self._window_max_age_sec = window_max_age_sec
        self._min_notes = min_notes
        self._notes: deque[tuple[int, float]] = deque()

    def add_note(self, midi_number: int, timestamp_sec: float) -> None:
        """Record a newly played note and trim the window to size/age limits."""
        self._notes.append((midi_number % 12, timestamp_sec))
        while len(self._notes) > self._window_note_count:
            self._notes.popleft()
        cutoff = timestamp_sec - self._window_max_age_sec
        while self._notes and self._notes[0][1] < cutoff:
            self._notes.popleft()

    def recent_pitch_classes(self) -> list[int]:
        """Pitch classes (0-11) of the notes currently in the window, oldest first."""
        return [pc for pc, _ in self._notes]

    def detect(self) -> KeyResult | None:
        """Estimate the current key/scale from the note window.

        Builds a normalized 12-bin pitch-class histogram and correlates it
        against all 24 rotated major/minor templates, returning the
        best-scoring match. Returns None if there aren't enough notes yet, or
        if the notes played so far are too uniform to discriminate a key
        (e.g. only one distinct pitch class).
        """
        if len(self._notes) < self._min_notes:
            return None

        histogram = np.zeros(12, dtype=float)
        for pc, _ in self._notes:
            histogram[pc] += 1.0
        if histogram.sum() == 0 or np.count_nonzero(histogram) < 2:
            return None
        histogram /= histogram.sum()

        best_score = -2.0
        best_root = 0
        best_is_major = True

        for root in range(12):
            for is_major, weights in ((True, MAJOR_WEIGHTS), (False, MINOR_WEIGHTS)):
                rotated = np.roll(weights, root)
                score = _safe_corrcoef(histogram, rotated)
                if score > best_score:
                    best_score = score
                    best_root = root
                    best_is_major = is_major

        intervals = MAJOR_INTERVALS if best_is_major else MINOR_INTERVALS
        scale_notes = [(best_root + iv) % 12 for iv in intervals]
        return KeyResult(best_root, best_is_major, best_score, scale_notes)


def _safe_corrcoef(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation of a and b, or -2.0 (lower than any real
    correlation) if either has zero variance, which would otherwise make
    numpy.corrcoef divide by zero."""
    if np.std(a) == 0 or np.std(b) == 0:
        return -2.0
    return float(np.corrcoef(a, b)[0, 1])

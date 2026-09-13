"""Spectral-flux based onset detection with adaptive threshold + debounce.

Spectral flux (half-wave-rectified frame-to-frame magnitude difference)
distinguishes a new pluck (broadband transient energy across many bins) from
vibrato/bend on a sustained note (energy shifts within a narrow band, low
flux). RMS is used as a secondary silence gate.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from nextnote.config import (
    MIN_NOTE_RMS,
    ONSET_FLUX_THRESHOLD_MULT,
    ONSET_HISTORY_SEC,
    ONSET_MIN_INTERVAL_SEC,
)


class OnsetDetector:
    """Detects the moment a new note starts (a pluck) within a continuous
    audio stream, so notes can be logged as discrete events rather than
    re-triggering for every analysis frame of a held note."""

    def __init__(
        self,
        history_sec: float = ONSET_HISTORY_SEC,
        threshold_mult: float = ONSET_FLUX_THRESHOLD_MULT,
        min_interval_sec: float = ONSET_MIN_INTERVAL_SEC,
        hop_duration_sec: float = 0.046,
    ):
        """
        Args:
            history_sec: length of the rolling flux history used to compute
                the adaptive onset threshold.
            threshold_mult: an onset fires when flux exceeds this multiple of
                the recent average flux.
            min_interval_sec: minimum time between onsets (debounce), so a
                single pluck's transient can't be double-counted.
            hop_duration_sec: time between analysis frames, used to size the
                flux history in frames rather than seconds.
        """
        self._threshold_mult = threshold_mult
        self._min_interval_sec = min_interval_sec
        history_len = max(1, int(history_sec / hop_duration_sec))
        self._flux_history: deque[float] = deque(maxlen=history_len)
        self._prev_mag: np.ndarray | None = None
        self._last_onset_time: float = float("-inf")

    def compute_flux(self, mag_spectrum: np.ndarray) -> float:
        """Spectral flux against the previous frame: the sum of only the
        positive (increasing) per-bin magnitude changes. A broadband
        transient like a pluck raises many bins at once, giving a large
        flux; a sustained note's energy mostly just shifts around, giving
        a small one."""
        if self._prev_mag is None or len(self._prev_mag) != len(mag_spectrum):
            self._prev_mag = mag_spectrum.copy()
            return 0.0
        diff = mag_spectrum - self._prev_mag
        flux = float(np.sum(np.maximum(diff, 0.0)))
        self._prev_mag = mag_spectrum.copy()
        return flux

    def process(self, mag_spectrum: np.ndarray, rms: float, timestamp_sec: float) -> bool:
        """Feed one analysis frame; returns True if this frame is a note onset.

        An onset requires: flux well above the recent rolling average
        (adaptive to the player's dynamics), the frame not being near-silent,
        and enough time having passed since the last onset (debounce).
        """
        flux = self.compute_flux(mag_spectrum)
        is_loud_enough = rms > MIN_NOTE_RMS
        has_enough_history = len(self._flux_history) >= max(3, self._flux_history.maxlen // 4)
        adaptive_threshold = (
            (sum(self._flux_history) / len(self._flux_history)) * self._threshold_mult
            if self._flux_history
            else float("inf")
        )
        is_flux_onset = has_enough_history and flux > adaptive_threshold
        debounced = (timestamp_sec - self._last_onset_time) > self._min_interval_sec

        self._flux_history.append(flux)

        if is_flux_onset and is_loud_enough and debounced:
            self._last_onset_time = timestamp_sec
            return True
        return False

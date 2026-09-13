"""Background QThread that owns audio capture + DSP and exposes results only
via Qt signals. Never touches any widget directly."""

from __future__ import annotations

import queue
import time

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from nextnote.audio.capture import AudioCapture
from nextnote.audio.onset import OnsetDetector
from nextnote.audio.pitch import estimate_pitch
from nextnote.audio.ring_buffer import RingBuffer
from nextnote.config import (
    BLOCK_SIZE,
    CHANNELS,
    DEVICE,
    FFT_WINDOW_SIZE,
    HOP_SIZE,
    MIN_NOTE_RMS,
    PITCH_CONFIRM_FRAMES,
    PITCH_CONFIRM_TOLERANCE_CENTS,
    QUEUE_MAX_CHUNKS,
    SAMPLE_RATE,
)
from nextnote.theory.notes import freq_to_midi, freq_to_note_and_cents


class _PendingConfirmation:
    """Confirms a note only once a few consecutive analysis frames agree on
    its pitch, so the noisy attack transient right after a pluck (where
    pitch estimates are unreliable) doesn't get logged as the note."""

    def __init__(self, tolerance_cents: float, required_frames: int):
        self._tolerance_cents = tolerance_cents
        self._required_frames = required_frames
        self._midi_estimates: list[int] = []

    def feed(self, freq: float | None) -> tuple[str, int] | None:
        """Feed one frame's pitch estimate (or None if silent/unvoiced).

        Resets the streak if the estimate jumps too far from the last one
        (tolerance_cents) or goes silent. Returns (note_name, midi_number)
        once enough consecutive frames have agreed, else None.
        """
        if freq is None:
            self._midi_estimates.clear()
            return None
        exact_midi = freq_to_midi(freq)
        nearest = round(exact_midi)
        if self._midi_estimates and abs(nearest - self._midi_estimates[-1]) > 0:
            cents_from_last_note = abs((exact_midi - self._midi_estimates[-1]) * 100.0)
            if cents_from_last_note > self._tolerance_cents:
                self._midi_estimates.clear()
        self._midi_estimates.append(nearest)
        if len(self._midi_estimates) >= self._required_frames:
            name, midi, _cents = freq_to_note_and_cents(freq)
            return name, midi
        return None


class AnalysisWorker(QThread):
    """Runs audio capture and all DSP (pitch/onset detection) on a background
    thread, publishing results only via Qt signals. Never touches any widget
    directly — the UI thread only ever reacts to these signals.

    Signals:
        pitch_updated(frequency_hz, rms_amplitude): emitted every analysis
            frame (~20/sec), including silence (frequency_hz will be 0.0).
        note_onset(frequency_hz, timestamp_sec): emitted the instant a new
            pluck is detected, before its pitch is confirmed.
        note_confirmed(note_name, midi_number, timestamp_sec): emitted once
            an onset's pitch has stabilized; this is what should be logged
            and fed into key detection.
        status_changed(status): human-readable status/error text.
    """

    pitch_updated = pyqtSignal(float, float)       # (frequency_hz, rms_amplitude)
    note_onset = pyqtSignal(float, float)            # (frequency_hz, timestamp_sec)
    note_confirmed = pyqtSignal(str, int, float)     # (note_name_with_octave, midi_number, timestamp_sec)
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=QUEUE_MAX_CHUNKS)
        self._capture = AudioCapture(SAMPLE_RATE, CHANNELS, BLOCK_SIZE, self._queue, DEVICE)
        self._ring_buffer = RingBuffer(FFT_WINDOW_SIZE + BLOCK_SIZE * 2)
        self._onset_detector = OnsetDetector(hop_duration_sec=HOP_SIZE / SAMPLE_RATE)
        self._pending: _PendingConfirmation | None = None
        self._samples_read_cursor = 0

    def run(self) -> None:
        """Thread entry point (called by QThread.start(), not directly).

        Starts audio capture, then loops pulling chunks off the queue and
        running one analysis frame every HOP_SIZE new samples, until stop()
        is called.
        """
        self._running = True
        try:
            self._capture.start()
        except Exception as exc:  # sounddevice raises various backend errors
            self.status_changed.emit(f"Audio error: {exc}")
            return

        self.status_changed.emit("Listening...")
        self._samples_read_cursor = 0

        while self._running:
            try:
                chunk = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self._ring_buffer.push(chunk)
            while self._ring_buffer.total_pushed - self._samples_read_cursor >= HOP_SIZE:
                self._samples_read_cursor += HOP_SIZE
                try:
                    self._analyze_frame()
                except Exception as exc:
                    # An uncaught exception here would escape QThread.run(),
                    # which PyQt5 treats as fatal (it calls abort() rather
                    # than letting a Python exception unwind through Qt's C++
                    # stack) -- so any unexpected DSP edge case must be
                    # contained here rather than crashing the whole app.
                    self.status_changed.emit(f"Analysis error (skipped a frame): {exc}")

        self._capture.stop()

    def _analyze_frame(self) -> None:
        """Run one full analysis pass on the latest FFT window: estimate
        pitch, check for a note onset, and feed any pending pitch
        confirmation, emitting signals as appropriate."""
        window = self._ring_buffer.get_last(FFT_WINDOW_SIZE)
        rms = float(np.sqrt(np.mean(window.astype(np.float64) ** 2)))
        freq, _freqs, mag = estimate_pitch(window, SAMPLE_RATE)

        now = self._samples_read_cursor / SAMPLE_RATE
        self.pitch_updated.emit(freq or 0.0, rms)

        is_onset = self._onset_detector.process(mag, rms, now)
        if is_onset:
            self.note_onset.emit(freq or 0.0, now)
            self._pending = _PendingConfirmation(PITCH_CONFIRM_TOLERANCE_CENTS, PITCH_CONFIRM_FRAMES)

        if self._pending is not None:
            result = self._pending.feed(freq if rms >= MIN_NOTE_RMS else None)
            if result is not None:
                name, midi = result
                self.note_confirmed.emit(name, midi, time.time())
                self._pending = None

    def stop(self) -> None:
        """Signal the run loop to exit and block until the thread has
        finished (and the audio stream has been closed)."""
        self._running = False
        self.wait()

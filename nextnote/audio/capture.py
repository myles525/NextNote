"""Microphone capture via sounddevice, delivering mono float32 chunks to a
thread-safe queue. Has zero Qt dependency so it's independently testable."""

from __future__ import annotations

import queue

import numpy as np
import sounddevice as sd


class AudioCapture:
    def __init__(
        self,
        samplerate: int,
        channels: int,
        blocksize: int,
        out_queue: "queue.Queue[np.ndarray]",
        device=None,
    ):
        self._samplerate = samplerate
        self._channels = channels
        self._blocksize = blocksize
        self._out_queue = out_queue
        self._device = device
        self._stream: sd.InputStream | None = None
        self.dropped_chunks = 0

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            pass  # ignore overflow/underflow flags rather than raising on the audio thread
        mono = indata[:, 0].copy()
        try:
            self._out_queue.put_nowait(mono)
        except queue.Full:
            self.dropped_chunks += 1

    def start(self) -> None:
        self._stream = sd.InputStream(
            samplerate=self._samplerate,
            channels=self._channels,
            blocksize=self._blocksize,
            dtype="float32",
            device=self._device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

"""Microphone capture via sounddevice, delivering mono float32 chunks to a
thread-safe queue. Has zero Qt dependency so it's independently testable."""

from __future__ import annotations

import queue

import numpy as np
import sounddevice as sd


class AudioCapture:
    """Wraps a sounddevice InputStream, pushing each incoming mono audio
    chunk onto a queue for a consumer to process on another thread."""

    def __init__(
        self,
        samplerate: int,
        channels: int,
        blocksize: int,
        out_queue: "queue.Queue[np.ndarray]",
        device=None,
    ):
        """
        Args:
            samplerate: capture sample rate in Hz.
            channels: number of input channels to open (mono capture uses
                just the first channel regardless of this value).
            blocksize: frames delivered per callback invocation.
            out_queue: queue that captured chunks are pushed onto; owned by
                the caller so this class has no Qt/threading dependencies of
                its own.
            device: sounddevice device index/name, or None for the system
                default input device.
        """
        self._samplerate = samplerate
        self._channels = channels
        self._blocksize = blocksize
        self._out_queue = out_queue
        self._device = device
        self._stream: sd.InputStream | None = None
        self.dropped_chunks = 0

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Invoked by PortAudio on its own real-time thread for each block of
        captured audio. Must stay fast and non-blocking: it only copies the
        first channel and enqueues it, dropping the chunk (counted in
        dropped_chunks) rather than blocking if the queue is full."""
        if status:
            pass  # ignore overflow/underflow flags rather than raising on the audio thread
        mono = indata[:, 0].copy()
        try:
            self._out_queue.put_nowait(mono)
        except queue.Full:
            self.dropped_chunks += 1

    def start(self) -> None:
        """Open and start the input stream. Raises whatever exception
        sounddevice/PortAudio raises if no suitable input device is available."""
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
        """Stop and close the input stream, if running."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

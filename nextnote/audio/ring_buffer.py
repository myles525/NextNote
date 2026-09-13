"""Rolling sample buffer that supports pushing chunks and reading the most
recent N samples (used to build FFT analysis windows)."""

from collections import deque

import numpy as np


class RingBuffer:
    """Accumulates variable-length audio chunks and lets callers pull a
    fixed-size window of the most recent samples for FFT analysis, without
    needing chunk boundaries to line up with the analysis window size."""

    def __init__(self, capacity: int):
        """capacity: maximum number of samples retained; older samples are
        dropped once this is exceeded."""
        self._capacity = capacity
        self._chunks: deque[np.ndarray] = deque()
        self._total_pushed = 0
        self._total_samples = 0

    def push(self, chunk: np.ndarray) -> None:
        """Append a new chunk of samples, discarding old chunks once the
        buffer exceeds its capacity."""
        self._chunks.append(chunk)
        self._total_pushed += len(chunk)
        self._total_samples += len(chunk)
        while self._total_samples > self._capacity and len(self._chunks) > 1:
            dropped = self._chunks.popleft()
            self._total_samples -= len(dropped)

    def get_last(self, n: int) -> np.ndarray:
        """Return the most recent n samples as a contiguous array, zero-padded
        at the start if fewer than n samples have been pushed so far."""
        if not self._chunks:
            return np.zeros(n, dtype=np.float32)
        buf = np.concatenate(self._chunks)
        if len(buf) < n:
            pad = np.zeros(n - len(buf), dtype=np.float32)
            return np.concatenate([pad, buf])
        return buf[-n:]

    @property
    def total_pushed(self) -> int:
        """Monotonically increasing count of samples ever pushed, used by
        callers to know when >= HOP_SIZE new samples have arrived."""
        return self._total_pushed

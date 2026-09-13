"""FFT-based pitch detection via Harmonic Product Spectrum (HPS).

A plucked guitar string's fundamental is often weaker than its 2nd/3rd
harmonic (especially on wound low strings), so naive magnitude-peak-picking
frequently locks onto the octave above. HPS multiplies compressed copies of
the spectrum together; only the true fundamental has energy lining up at
every harmonic position, so it wins even when its own bin isn't the tallest
in the raw spectrum. Sub-bin accuracy then comes from parabolic interpolation
around the winning peak using the raw (non-HPS) magnitude spectrum.
"""

from __future__ import annotations

import math

import numpy as np

from nextnote.config import (
    HPS_HARMONICS,
    MAX_FREQ_HZ,
    MIN_FREQ_HZ,
    MIN_NOTE_RMS,
    ZERO_PAD_FACTOR,
)


def compute_magnitude_and_hps(
    samples: np.ndarray,
    sample_rate: int,
    n_harmonics: int = HPS_HARMONICS,
    zero_pad_factor: int = ZERO_PAD_FACTOR,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Window, FFT, and build the Harmonic Product Spectrum for a sample block.

    Applies a Hann window (reduces spectral leakage from the block edges),
    zero-pads before the FFT (smooths the peak shape for later interpolation),
    then computes the HPS by multiplying n_harmonics downsampled copies of the
    magnitude spectrum together — this reinforces the true fundamental (whose
    harmonics line up across every downsampled copy) relative to a spectrum
    peak at a harmonic, which won't.

    Returns:
        (freqs, magnitude_spectrum, hps_spectrum) — all the same length,
        indexed by FFT bin.
    """
    n = len(samples)
    window = np.hanning(n)
    windowed = samples * window

    padded_n = n * zero_pad_factor
    spectrum = np.fft.rfft(windowed, n=padded_n)
    mag = np.abs(spectrum)
    freqs = np.fft.rfftfreq(padded_n, d=1.0 / sample_rate)

    hps = mag.copy()
    for h in range(2, n_harmonics + 1):
        downsampled = mag[::h]
        hps[: len(downsampled)] *= downsampled
        hps[len(downsampled):] = 0.0

    return freqs, mag, hps


def find_fundamental_freq(
    freqs: np.ndarray,
    mag: np.ndarray,
    hps: np.ndarray,
    min_freq: float = MIN_FREQ_HZ,
    max_freq: float = MAX_FREQ_HZ,
) -> float | None:
    """Locate the fundamental frequency from an HPS spectrum.

    Picks the highest HPS peak within [min_freq, max_freq] (restricting the
    search to the guitar's playable range avoids picking up rumble or
    ultrasonic noise), then refines that peak's frequency with parabolic
    interpolation over the raw magnitude spectrum's neighboring bins — this
    is what gives cents-level accuracy despite a much coarser raw FFT bin
    spacing.

    Returns None if there's no energy in range (e.g. silence).
    """
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    if not np.any(mask):
        return None

    masked_indices = np.nonzero(mask)[0]
    masked_hps = hps[masked_indices]
    if masked_hps.max() <= 0:
        return None

    peak_idx = masked_indices[np.argmax(masked_hps)]
    if peak_idx <= 0 or peak_idx >= len(mag) - 1:
        freq = float(freqs[peak_idx])
        return freq if math.isfinite(freq) and freq > 0 else None

    alpha, beta, gamma = mag[peak_idx - 1], mag[peak_idx], mag[peak_idx + 1]
    denom = alpha - 2 * beta + gamma
    # A near-flat peak (denom close to but not exactly zero) makes the
    # parabolic fit blow up; the interpolation is only mathematically valid
    # for |p| <= 0.5, so clamp rather than let a huge offset through.
    if abs(denom) < 1e-9:
        true_bin = float(peak_idx)
    else:
        p = 0.5 * (alpha - gamma) / denom
        p = max(-0.5, min(0.5, p))
        true_bin = peak_idx + p

    freq_resolution = freqs[1] - freqs[0]
    freq = true_bin * freq_resolution
    return freq if math.isfinite(freq) and freq > 0 else None


def estimate_pitch(samples: np.ndarray, sample_rate: int) -> tuple[float | None, np.ndarray, np.ndarray]:
    """High-level convenience: windowing + HPS + peak-pick + interpolate.

    Returns (frequency_or_none, freqs, mag) so callers (e.g. the onset
    detector) can reuse the same FFT's magnitude spectrum without recomputing
    it.
    """
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    freqs, mag, hps = compute_magnitude_and_hps(samples, sample_rate)
    if rms < MIN_NOTE_RMS:
        return None, freqs, mag
    freq = find_fundamental_freq(freqs, mag, hps)
    return freq, freqs, mag

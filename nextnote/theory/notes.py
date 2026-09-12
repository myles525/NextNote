"""Frequency <-> MIDI <-> note name conversions (equal temperament, A4=440Hz)."""

import math

from nextnote.config import A4_FREQ

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def freq_to_midi(freq: float, a4_freq: float = A4_FREQ) -> float:
    """Fractional MIDI note number for a frequency (69 = A4)."""
    return 69.0 + 12.0 * math.log2(freq / a4_freq)


def midi_to_freq(midi: float, a4_freq: float = A4_FREQ) -> float:
    return a4_freq * (2.0 ** ((midi - 69.0) / 12.0))


def midi_to_note_name(midi_number: int) -> str:
    """e.g. 64 -> 'E4' (MIDI 60 = C4, standard scientific pitch convention)."""
    name = NOTE_NAMES[midi_number % 12]
    octave = midi_number // 12 - 1
    return f"{name}{octave}"


def freq_to_note_and_cents(freq: float, a4_freq: float = A4_FREQ) -> tuple[str, int, float]:
    """Returns (note_name_with_octave, nearest_midi_number, cents_deviation).

    cents_deviation is bounded to roughly [-50, 50] by construction, since it's
    the remainder after rounding to the nearest semitone.
    """
    exact_midi = freq_to_midi(freq, a4_freq)
    nearest = round(exact_midi)
    cents = (exact_midi - nearest) * 100.0
    return midi_to_note_name(nearest), nearest, cents


def pitch_class(midi_number: int) -> int:
    return midi_number % 12

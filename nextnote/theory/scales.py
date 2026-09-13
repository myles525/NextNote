"""Fixed scale definitions and helpers for the manual scale-picker workflow.

The player explicitly chooses a root note and scale type (rather than the
app guessing a key from what's been played); every confirmed note is then
checked against that fixed scale, and an out-of-scale note gets a
nearest-in-scale suggestion.
"""

from __future__ import annotations

from nextnote.theory.notes import NOTE_NAMES, midi_to_note_name, pitch_class

SCALE_DEFINITIONS: dict[str, list[int]] = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Natural Minor": [0, 2, 3, 5, 7, 8, 10],
    "Major Pentatonic": [0, 2, 4, 7, 9],
    "Minor Pentatonic": [0, 3, 5, 7, 10],
    "Blues": [0, 3, 5, 6, 7, 10],
}


def scale_pitch_classes(root_pitch_class: int, scale_type: str) -> list[int]:
    """Pitch classes (0-11) making up the given scale, root first."""
    intervals = SCALE_DEFINITIONS[scale_type]
    return [(root_pitch_class + iv) % 12 for iv in intervals]


def scale_name(root_pitch_class: int, scale_type: str) -> str:
    """Human-readable name, e.g. 'C Major'."""
    return f"{NOTE_NAMES[root_pitch_class]} {scale_type}"


def nearest_in_scale_note(midi_number: int, scale_pcs: list[int]) -> tuple[str, int]:
    """Find the closest note (by semitone distance) to midi_number whose
    pitch class is in scale_pcs. If midi_number is already in the scale,
    returns it unchanged (distance 0).

    Searches outward by increasing distance, checking the lower candidate
    before the higher one at each distance -- an arbitrary but consistent
    tie-break for when both directions are equally close.
    """
    if pitch_class(midi_number) in scale_pcs:
        return midi_to_note_name(midi_number), midi_number

    distance = 1
    while distance <= 12:
        for candidate in (midi_number - distance, midi_number + distance):
            if pitch_class(candidate) in scale_pcs:
                return midi_to_note_name(candidate), candidate
        distance += 1

    # Unreachable: every scale above has at least one pitch class, and 12
    # consecutive semitones in either direction cover all 12 pitch classes.
    return midi_to_note_name(midi_number), midi_number

"""Next-note-to-play recommendations from a detected key/scale."""

from __future__ import annotations

from nextnote.config import RECENCY_DECAY_NOTES, RECENCY_PENALTY, RECOMMEND_COUNT
from nextnote.theory.key_detection import KeyResult
from nextnote.theory.notes import NOTE_NAMES


def recommend_next_notes(
    key_result: KeyResult | None,
    recent_pitch_classes: list[int],
    count: int = RECOMMEND_COUNT,
    recency_decay_notes: int = RECENCY_DECAY_NOTES,
    recency_penalty: float = RECENCY_PENALTY,
) -> list[str]:
    """Suggest scale tones worth playing next, favoring ones played less recently.

    Every note in the detected scale starts at weight 1.0. Notes found in the
    recent-history window get penalized (most recently played = most
    penalized), so the ranking nudges the player toward underused scale
    tones. The tonic and dominant get a small bonus so suggestions still
    feel musically anchored to the key.

    Args:
        key_result: the currently detected key/scale, or None if no key has
            been detected yet (returns an empty list in that case).
        recent_pitch_classes: pitch classes (0-11) of recently played notes,
            oldest first.
        count: how many notes to suggest.
        recency_decay_notes: how many of the most recent notes count as
            "recently played" for the penalty.
        recency_penalty: the weight multiplier applied to a note played most
            recently (closer to 0 = stronger penalty).

    Returns:
        Note names (no octave), best suggestion first.
    """
    if key_result is None:
        return []

    scale = key_result.scale_notes
    recent_window = recent_pitch_classes[-recency_decay_notes:]
    dominant = (key_result.root_pitch_class + 7) % 12

    weights: dict[int, float] = {}
    for pc in scale:
        weight = 1.0
        if pc in recent_window:
            idx_from_end = recent_window[::-1].index(pc)  # 0 = just played
            recency_factor = idx_from_end / max(1, len(recent_window))
            weight = recency_penalty + (1.0 - recency_penalty) * recency_factor
        if pc == key_result.root_pitch_class or pc == dominant:
            weight *= 1.15
        weights[pc] = weight

    ranked = sorted(scale, key=lambda pc: weights[pc], reverse=True)
    return [NOTE_NAMES[pc] for pc in ranked[:count]]

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

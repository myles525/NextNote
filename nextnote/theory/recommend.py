"""Next-note-to-play recommendations within a fixed, manually chosen scale."""

from __future__ import annotations

from nextnote.config import RECENCY_DECAY_NOTES, RECENCY_PENALTY, RECOMMEND_COUNT
from nextnote.theory.notes import NOTE_NAMES


def recommend_next_notes(
    scale_pcs: list[int],
    recent_pitch_classes: list[int],
    count: int = RECOMMEND_COUNT,
    recency_decay_notes: int = RECENCY_DECAY_NOTES,
    recency_penalty: float = RECENCY_PENALTY,
) -> list[str]:
    """Rank the current scale's notes by how worth playing they are right now.

    Every scale tone starts at weight 1.0. Notes found in the recent-history
    window get penalized (the most recently played note is penalized most),
    so the ranking nudges the player toward underused scale tones. The root
    and fifth get a small bonus so suggestions still feel musically anchored.

    Args:
        scale_pcs: pitch classes (0-11) of the currently selected scale, root
            first (as returned by theory.scales.scale_pitch_classes).
        recent_pitch_classes: pitch classes of recently played notes, oldest
            first.
        count: how many notes to suggest.
        recency_decay_notes: how many of the most recent notes count as
            "recently played" for the penalty.
        recency_penalty: weight multiplier applied to a note played most
            recently (closer to 0 = stronger penalty).

    Returns:
        Note names (no octave), best suggestion first.
    """
    if not scale_pcs:
        return []

    root = scale_pcs[0]
    dominant = (root + 7) % 12
    recent_window = recent_pitch_classes[-recency_decay_notes:]

    weights: dict[int, float] = {}
    for pc in scale_pcs:
        weight = 1.0
        if pc in recent_window:
            idx_from_end = recent_window[::-1].index(pc)  # 0 = just played
            recency_factor = idx_from_end / max(1, len(recent_window))
            weight = recency_penalty + (1.0 - recency_penalty) * recency_factor
        if pc == root or pc == dominant:
            weight *= 1.15
        weights[pc] = weight

    ranked = sorted(scale_pcs, key=lambda pc: weights[pc], reverse=True)
    return [NOTE_NAMES[pc] for pc in ranked[:count]]

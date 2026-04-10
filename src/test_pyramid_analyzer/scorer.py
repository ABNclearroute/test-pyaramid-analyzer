"""Weighted scoring engine — aggregates signals into per-type score vectors."""
from __future__ import annotations

from typing import Dict, List

from .models import TEST_TYPES, Signal


class WeightedScorer:
    """Sum signal weights into a score for each test type.

    The output is a raw (non-normalised) ``{type: score}`` dict.  Normalisation
    and confidence calculation happen in :class:`~confidence.ConfidenceCalculator`
    so that each concern stays in its own module.
    """

    def score(self, signals: List[Signal]) -> Dict[str, float]:
        """Return a mapping of test type → cumulative weight."""
        scores: Dict[str, float] = {t: 0.0 for t in TEST_TYPES}
        for signal in signals:
            if signal.test_type in scores:
                scores[signal.test_type] += signal.weight
        return scores

    def normalise(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Return fractional scores that sum to 1.0, or all-zeros if no signals."""
        total = sum(scores.values())
        if total == 0.0:
            return dict(scores)
        return {t: v / total for t, v in scores.items()}

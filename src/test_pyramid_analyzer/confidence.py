"""Confidence calculation and ambiguity detection."""
from __future__ import annotations


class ConfidenceCalculator:
    """Turn raw score vectors into a (classification, confidence, is_ambiguous) triple.

    Confidence is defined as::

        confidence = top_score / total_score

    Ambiguity is declared when the two highest-scoring types are within
    ``ambiguity_threshold`` of each other (as a fraction of the total score),
    AND the winning confidence is below ``(1 - ambiguity_threshold)``.
    """

    def __init__(
        self,
        ambiguity_threshold: float = 0.15,
        min_confidence: float = 0.30,
    ) -> None:
        self.ambiguity_threshold = ambiguity_threshold
        self.min_confidence = min_confidence

    def calculate(self, scores: dict[str, float]) -> tuple[str, float, bool]:
        """Return *(classification, confidence, is_ambiguous)*.

        *classification* is one of: ``unit``, ``integration``, ``e2e``,
        ``ambiguous``, or ``unknown``.
        """
        total = sum(scores.values())
        if total == 0.0:
            return "unknown", 0.0, False

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top_type, top_score = ranked[0]
        _, second_score = ranked[1] if len(ranked) > 1 else ("", 0.0)

        confidence = top_score / total

        if confidence < self.min_confidence:
            return "unknown", confidence, False

        # Two types are close → ambiguous
        gap_fraction = (top_score - second_score) / total
        is_ambiguous = (
            second_score > 0.0
            and gap_fraction < self.ambiguity_threshold
        )

        classification = "ambiguous" if is_ambiguous else top_type
        return classification, round(confidence, 4), is_ambiguous

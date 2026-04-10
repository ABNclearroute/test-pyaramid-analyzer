"""Tests for the weighted scoring engine."""
import pytest

from test_pyramid_analyzer.models import Signal
from test_pyramid_analyzer.scorer import WeightedScorer


@pytest.fixture
def scorer():
    return WeightedScorer()


def make_signal(test_type: str, weight: float) -> Signal:
    return Signal(test_type=test_type, source="test", name="s", weight=weight)


class TestWeightedScorer:
    def test_empty_signals_returns_zeros(self, scorer):
        scores = scorer.score([])
        assert scores == {"unit": 0.0, "integration": 0.0, "e2e": 0.0}

    def test_single_unit_signal(self, scorer):
        scores = scorer.score([make_signal("unit", 2.5)])
        assert scores["unit"] == pytest.approx(2.5)
        assert scores["integration"] == 0.0
        assert scores["e2e"] == 0.0

    def test_multiple_signals_summed(self, scorer):
        signals = [
            make_signal("unit", 2.0),
            make_signal("unit", 1.5),
            make_signal("integration", 3.0),
        ]
        scores = scorer.score(signals)
        assert scores["unit"] == pytest.approx(3.5)
        assert scores["integration"] == pytest.approx(3.0)
        assert scores["e2e"] == 0.0

    def test_unknown_test_type_ignored(self, scorer):
        scores = scorer.score([make_signal("unknown_type", 5.0)])
        assert sum(scores.values()) == 0.0

    def test_normalise_sums_to_one(self, scorer):
        raw = {"unit": 6.0, "integration": 3.0, "e2e": 1.0}
        norm = scorer.normalise(raw)
        assert sum(norm.values()) == pytest.approx(1.0)
        assert norm["unit"] == pytest.approx(0.6)

    def test_normalise_all_zeros_stays_zero(self, scorer):
        raw = {"unit": 0.0, "integration": 0.0, "e2e": 0.0}
        norm = scorer.normalise(raw)
        assert all(v == 0.0 for v in norm.values())

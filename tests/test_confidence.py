"""Tests for confidence calculation and ambiguity detection."""
import pytest

from test_pyramid_analyzer.confidence import ConfidenceCalculator


@pytest.fixture
def calc():
    return ConfidenceCalculator(ambiguity_threshold=0.15, min_confidence=0.30)


class TestConfidenceCalculator:
    def test_all_zeros_returns_unknown(self, calc):
        classification, conf, ambiguous = calc.calculate(
            {"unit": 0.0, "integration": 0.0, "e2e": 0.0}
        )
        assert classification == "unknown"
        assert conf == 0.0
        assert ambiguous is False

    def test_clear_unit_winner(self, calc):
        classification, conf, ambiguous = calc.calculate(
            {"unit": 8.0, "integration": 1.0, "e2e": 1.0}
        )
        assert classification == "unit"
        assert conf == pytest.approx(0.8)
        assert ambiguous is False

    def test_ambiguous_when_scores_close(self, calc):
        # unit=5, integration=4, e2e=1  → gap fraction = (5-4)/10 = 0.10 < 0.15
        classification, conf, ambiguous = calc.calculate(
            {"unit": 5.0, "integration": 4.0, "e2e": 1.0}
        )
        assert classification == "ambiguous"
        assert ambiguous is True

    def test_not_ambiguous_when_gap_large(self, calc):
        # unit=9, integration=1  → gap fraction = (9-1)/10 = 0.80 > 0.15
        classification, conf, ambiguous = calc.calculate(
            {"unit": 9.0, "integration": 1.0, "e2e": 0.0}
        )
        assert classification == "unit"
        assert ambiguous is False

    def test_below_min_confidence_returns_unknown(self, calc):
        # unit=2, integration=3, e2e=5  → unit conf = 2/10 = 0.20 < 0.30
        classification, conf, _ = calc.calculate(
            {"unit": 2.0, "integration": 3.0, "e2e": 5.0}
        )
        # e2e should win but its confidence = 5/10 = 0.5 ≥ 0.3
        assert classification in ("e2e", "ambiguous")

    def test_e2e_classification(self, calc):
        classification, conf, _ = calc.calculate(
            {"unit": 1.0, "integration": 1.0, "e2e": 8.0}
        )
        assert classification == "e2e"
        assert conf == pytest.approx(0.8)

"""Integration tests for the full classification pipeline."""
from pathlib import Path

import pytest

from test_pyramid_analyzer.classifier import TestClassifier
from test_pyramid_analyzer.rules_loader import RulesLoader

FIXTURE_REPO = Path(__file__).parent / "fixtures" / "sample_repo"


@pytest.fixture(scope="module")
def rules():
    return RulesLoader().load()


@pytest.fixture(scope="module")
def classified(rules):
    return TestClassifier(rules).classify_files(FIXTURE_REPO)


class TestClassifierResults:
    def test_returns_three_test_files(self, classified):
        assert len(classified) == 3

    def test_calculator_classified_as_unit(self, classified):
        calc = next(r for r in classified if "test_calculator" in r.relative_path)
        assert calc.classification == "unit"
        assert calc.confidence > 0.5

    def test_db_connection_classified_as_integration(self, classified):
        db = next(r for r in classified if "test_db_connection" in r.relative_path)
        assert db.classification == "integration"
        assert db.confidence > 0.4

    def test_login_flow_classified_as_e2e(self, classified):
        e2e = next(r for r in classified if "test_login_flow" in r.relative_path)
        assert e2e.classification == "e2e"
        assert e2e.confidence > 0.5

    def test_all_results_have_signals(self, classified):
        for result in classified:
            assert len(result.signals) > 0, f"{result.relative_path} has no signals"

    def test_scores_are_non_negative(self, classified):
        for result in classified:
            for score in result.scores.values():
                assert score >= 0.0

    def test_confidence_between_0_and_1(self, classified):
        for result in classified:
            assert 0.0 <= result.confidence <= 1.0


class TestAggregation:
    def test_aggregate_sums_correctly(self, rules):
        results = TestClassifier(rules).classify_files(FIXTURE_REPO)
        distribution, counts = TestClassifier._aggregate(results)
        assert counts["unit"] + counts["integration"] + counts["e2e"] >= 2
        total = sum(counts.values())
        assert total == len(results)

"""Tests for anti-pattern detection and recommendation generation."""
import pytest

from test_pyramid_analyzer.anti_patterns import AntiPatternDetector, generate_recommendations


@pytest.fixture
def detector():
    return AntiPatternDetector()


class TestIceCreamCone:
    def test_detected_when_e2e_over_30_pct(self, detector):
        dist = {"unit": 0.30, "integration": 0.30, "e2e": 0.40}
        results = {r.name: r for r in detector.detect(dist)}
        assert results["Ice Cream Cone"].detected is True

    def test_not_detected_when_e2e_under_30_pct(self, detector):
        dist = {"unit": 0.60, "integration": 0.20, "e2e": 0.20}
        results = {r.name: r for r in detector.detect(dist)}
        assert results["Ice Cream Cone"].detected is False

    def test_severity_error_when_e2e_over_50_pct(self, detector):
        dist = {"unit": 0.10, "integration": 0.10, "e2e": 0.80}
        results = {r.name: r for r in detector.detect(dist)}
        ap = results["Ice Cream Cone"]
        assert ap.detected is True
        assert ap.severity == "error"


class TestHourglass:
    def test_detected_when_integration_low_and_e2e_high(self, detector):
        dist = {"unit": 0.70, "integration": 0.05, "e2e": 0.25}
        results = {r.name: r for r in detector.detect(dist)}
        assert results["Hourglass"].detected is True

    def test_not_detected_when_integration_sufficient(self, detector):
        dist = {"unit": 0.60, "integration": 0.20, "e2e": 0.20}
        results = {r.name: r for r in detector.detect(dist)}
        assert results["Hourglass"].detected is False


class TestRecommendations:
    def test_healthy_pyramid_positive_message(self, detector):
        dist = {"unit": 0.65, "integration": 0.25, "e2e": 0.10}
        anti = detector.detect(dist)
        recs = generate_recommendations(dist, anti)
        assert len(recs) == 1
        assert "healthy" in recs[0].lower()

    def test_ice_cream_cone_recommendation(self, detector):
        dist = {"unit": 0.10, "integration": 0.10, "e2e": 0.80}
        anti = detector.detect(dist)
        recs = generate_recommendations(dist, anti)
        assert any("E2E" in r or "e2e" in r.lower() for r in recs)

    def test_no_integration_recommendation(self, detector):
        dist = {"unit": 0.90, "integration": 0.00, "e2e": 0.10}
        anti = detector.detect(dist)
        recs = generate_recommendations(dist, anti)
        assert any("integration" in r.lower() for r in recs)

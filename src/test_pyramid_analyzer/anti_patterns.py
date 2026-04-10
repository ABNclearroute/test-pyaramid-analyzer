"""Anti-pattern detection and recommendation generation."""
from __future__ import annotations

from .models import AntiPatternResult

# ---------------------------------------------------------------------------
# Target distribution thresholds (healthy pyramid)
# ---------------------------------------------------------------------------
_UNIT_TARGET_MIN = 0.50
_INTEGRATION_TARGET_MIN = 0.20
_E2E_TARGET_MAX = 0.30

# Anti-pattern thresholds
_ICE_CREAM_E2E_THRESHOLD = 0.30
_HOURGLASS_INTEGRATION_MAX = 0.10
_HOURGLASS_E2E_MIN = 0.20
_TROPHY_UNIT_MAX = 0.15
_TROPHY_INTEGRATION_MIN = 0.50


class AntiPatternDetector:
    """Evaluate a distribution dict and return a list of anti-pattern results.

    The distribution values are fractions (0.0–1.0) for each test type:
    ``{"unit": 0.6, "integration": 0.2, "e2e": 0.1, ...}``.
    """

    def detect(self, distribution: dict[str, float]) -> list[AntiPatternResult]:
        checkers = [
            self._ice_cream_cone,
            self._hourglass,
            self._testing_trophy,
            self._no_unit_tests,
            self._no_integration_tests,
        ]
        return [checker(distribution) for checker in checkers]

    # ------------------------------------------------------------------
    # Individual anti-pattern checks
    # ------------------------------------------------------------------

    @staticmethod
    def _ice_cream_cone(dist: dict[str, float]) -> AntiPatternResult:
        """E2E tests dominate — the pyramid is inverted."""
        e2e = dist.get("e2e", 0.0)
        unit = dist.get("unit", 0.0)
        detected = e2e > _ICE_CREAM_E2E_THRESHOLD
        return AntiPatternResult(
            name="Ice Cream Cone",
            description=(
                "E2E tests make up more than 30 % of the suite. "
                "High-level tests are expensive to run and maintain."
            ),
            detected=detected,
            details=f"E2E: {e2e:.1%}  |  Unit: {unit:.1%}" if detected else "",
            severity="error" if e2e > 0.50 else "warning",
        )

    @staticmethod
    def _hourglass(dist: dict[str, float]) -> AntiPatternResult:
        """Narrow integration layer with a heavy E2E layer."""
        integration = dist.get("integration", 0.0)
        e2e = dist.get("e2e", 0.0)
        detected = integration < _HOURGLASS_INTEGRATION_MAX and e2e > _HOURGLASS_E2E_MIN
        return AntiPatternResult(
            name="Hourglass",
            description=(
                "Very few integration tests (<10 %) but a large E2E layer (>20 %). "
                "Service boundaries are untested at the right level."
            ),
            detected=detected,
            details=(
                f"Integration: {integration:.1%}  |  E2E: {e2e:.1%}" if detected else ""
            ),
            severity="warning",
        )

    @staticmethod
    def _testing_trophy(dist: dict[str, float]) -> AntiPatternResult:
        """Very few unit tests, integration tests dominate (Testing Trophy shape)."""
        unit = dist.get("unit", 0.0)
        integration = dist.get("integration", 0.0)
        detected = unit < _TROPHY_UNIT_MAX and integration > _TROPHY_INTEGRATION_MIN
        return AntiPatternResult(
            name="Testing Trophy (over-rotated)",
            description=(
                "Unit tests are almost absent (<15 %) while integration tests dominate (>50 %). "
                "Individual components are not being tested in isolation."
            ),
            detected=detected,
            details=(
                f"Unit: {unit:.1%}  |  Integration: {integration:.1%}" if detected else ""
            ),
            severity="warning",
        )

    @staticmethod
    def _no_unit_tests(dist: dict[str, float]) -> AntiPatternResult:
        unit = dist.get("unit", 0.0)
        detected = unit < 0.20
        return AntiPatternResult(
            name="Insufficient Unit Tests",
            description="Unit tests are below 20 % — individual functions lack isolated coverage.",
            detected=detected,
            details=f"Unit: {unit:.1%}" if detected else "",
            severity="warning",
        )

    @staticmethod
    def _no_integration_tests(dist: dict[str, float]) -> AntiPatternResult:
        integration = dist.get("integration", 0.0)
        total_tests = sum(v for k, v in dist.items() if k in ("unit", "integration", "e2e"))
        # Only flag if there are enough total tests to form an opinion
        detected = total_tests > 0 and integration == 0.0
        return AntiPatternResult(
            name="No Integration Tests",
            description="Zero integration tests detected — service boundaries are not validated.",
            detected=detected,
            details="Integration: 0 %" if detected else "",
            severity="warning",
        )


# ---------------------------------------------------------------------------
# Recommendation generator
# ---------------------------------------------------------------------------

def generate_recommendations(
    distribution: dict[str, float],
    anti_patterns: list[AntiPatternResult],
) -> list[str]:
    """Return an ordered list of actionable recommendations based on the report."""
    detected_names = {ap.name for ap in anti_patterns if ap.detected}
    recs: list[str] = []

    unit = distribution.get("unit", 0.0)
    integration = distribution.get("integration", 0.0)
    e2e = distribution.get("e2e", 0.0)

    if "Ice Cream Cone" in detected_names:
        recs.append(
            f"Reduce E2E tests ({e2e:.1%} → target <{_ICE_CREAM_E2E_THRESHOLD:.0%}). "
            "Replace high-cost E2E scenarios with focused unit or integration tests."
        )
        recs.append(
            "Audit E2E tests for single-responsibility issues — "
            "tests that validate one function should be unit tests."
        )

    if "Hourglass" in detected_names:
        recs.append(
            f"Add integration tests ({integration:.1%} → target >{_INTEGRATION_TARGET_MIN:.0%}). "
            "Use TestContainers, WireMock, or in-memory databases to test service boundaries."
        )

    if "Testing Trophy (over-rotated)" in detected_names:
        recs.append(
            f"Add unit tests ({unit:.1%} → target >{_UNIT_TARGET_MIN:.0%}). "
            "Cover pure functions and business logic with fast, isolated unit tests."
        )

    trophy_detected = "Testing Trophy (over-rotated)" not in detected_names
    if "Insufficient Unit Tests" in detected_names and trophy_detected:
        recs.append(
            f"Increase unit test coverage ({unit:.1%} → target >{_UNIT_TARGET_MIN:.0%}). "
            "Unit tests are the fastest feedback loop and should dominate the pyramid."
        )

    if "No Integration Tests" in detected_names:
        recs.append(
            "Introduce integration tests for critical service boundaries "
            "(database access, external APIs, message queues)."
        )

    if not recs:
        # Positive feedback for a healthy pyramid
        recs.append(
            "Test pyramid looks healthy! "
            f"Unit: {unit:.1%}, Integration: {integration:.1%}, E2E: {e2e:.1%}. "
            "Continue maintaining this distribution as the codebase grows."
        )

    return recs

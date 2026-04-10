"""Classification orchestrator — wires scanner → parser → scorer → confidence."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from .confidence import ConfidenceCalculator
from .models import AnalysisReport, TestFileResult
from .parser import SignalExtractor
from .scanner import TestFileScanner
from .scorer import WeightedScorer

logger = logging.getLogger(__name__)


class TestClassifier:
    """Orchestrate the full classification pipeline for a repository.

    Usage::

        rules = RulesLoader(custom_path).load()
        report = TestClassifier(rules).analyse(Path("/path/to/repo"))
    """

    def __init__(self, rules: dict, debug: bool = False) -> None:
        self._rules = rules
        self._debug = debug
        scoring_cfg = rules.get("scoring", {})

        self._scanner = TestFileScanner(rules)
        self._extractor = SignalExtractor(rules)
        self._scorer = WeightedScorer()
        self._confidence = ConfidenceCalculator(
            ambiguity_threshold=float(scoring_cfg.get("ambiguity_threshold", 0.15)),
            min_confidence=float(scoring_cfg.get("min_confidence", 0.30)),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_files(self, repo_path: Path) -> list[TestFileResult]:
        """Scan *repo_path* and return a classified result for every test file."""
        found = self._scanner.scan(repo_path)
        results: list[TestFileResult] = []
        for file_path, language in found:
            result = self._classify_single(file_path, language, repo_path)
            if self._debug:
                self._log_debug(result)
            results.append(result)
        return results

    def build_report(
        self,
        repo_path: Path,
        ci_pipeline=None,
        anti_patterns: list | None = None,
        recommendations: list[str] | None = None,
    ) -> AnalysisReport:
        """Run the full pipeline and return a populated :class:`AnalysisReport`."""
        test_files = self.classify_files(repo_path)
        distribution, counts = self._aggregate(test_files)

        return AnalysisReport(
            repo_path=str(repo_path.resolve()),
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            total_test_files=len(test_files),
            test_files=test_files,
            distribution=distribution,
            counts=counts,
            anti_patterns=anti_patterns or [],
            recommendations=recommendations or [],
            ci_pipeline=ci_pipeline,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify_single(
        self, file_path: Path, language: str, repo_root: Path
    ) -> TestFileResult:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("Cannot read %s: %s", file_path, exc)
            content = ""

        signals = self._extractor.extract(file_path, language, content)
        raw_scores = self._scorer.score(signals)
        classification, confidence, is_ambiguous = self._confidence.calculate(raw_scores)

        try:
            relative = str(file_path.relative_to(repo_root))
        except ValueError:
            relative = str(file_path)

        return TestFileResult(
            path=file_path,
            relative_path=relative,
            language=language,
            signals=signals,
            scores=raw_scores,
            classification=classification,
            confidence=confidence,
            is_ambiguous=is_ambiguous,
        )

    @staticmethod
    def _aggregate(
        results: list[TestFileResult],
    ) -> tuple[dict[str, float], dict[str, int]]:
        """Compute distribution fractions and raw counts from classified results."""
        from .models import TEST_TYPES

        counts: dict[str, int] = {t: 0 for t in (*TEST_TYPES, "ambiguous", "unknown")}
        for r in results:
            counts[r.classification] = counts.get(r.classification, 0) + 1

        total = len(results)
        distribution: dict[str, float] = {
            t: (counts.get(t, 0) / total) if total else 0.0
            for t in counts
        }
        return distribution, counts

    def _log_debug(self, result: TestFileResult) -> None:
        logger.debug(
            "[%s] %s → %s (conf=%.2f) signals=%d scores=%s",
            result.language,
            result.relative_path,
            result.classification,
            result.confidence,
            len(result.signals),
            {k: round(v, 2) for k, v in result.scores.items()},
        )

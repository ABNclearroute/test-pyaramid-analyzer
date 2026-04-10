"""Core data models for the test pyramid analyzer."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

TEST_TYPES = ("unit", "integration", "e2e")


@dataclass
class Signal:
    """A single classification signal extracted from a test file."""

    test_type: str        # "unit" | "integration" | "e2e"
    source: str           # "path_pattern" | "framework" | "code_pattern"
    name: str             # human-readable signal name
    weight: float         # positive contribution toward test_type
    matched_text: str = ""


@dataclass
class TestFileResult:
    """Classification result for a single test file."""

    path: Path
    relative_path: str
    language: str
    signals: List[Signal] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    classification: str = "unknown"   # unit | integration | e2e | ambiguous | unknown
    confidence: float = 0.0
    is_ambiguous: bool = False

    @property
    def dominant_signals(self) -> List[Signal]:
        """Return signals that match the final classification."""
        return [s for s in self.signals if s.test_type == self.classification]


@dataclass
class CIStep:
    """A test-related step extracted from a CI pipeline."""

    name: str
    command: str
    test_type_hint: Optional[str] = None


@dataclass
class CIPipelineInfo:
    """Parsed information from a CI pipeline configuration file."""

    source_file: str
    tool: str                            # "github_actions"
    steps: List[CIStep] = field(default_factory=list)


@dataclass
class AntiPatternResult:
    """Result of a single anti-pattern check."""

    name: str
    description: str
    detected: bool
    details: str = ""
    severity: str = "warning"           # "warning" | "error"


@dataclass
class AnalysisReport:
    """Top-level report produced by a full repository analysis."""

    repo_path: str
    timestamp: str
    total_test_files: int
    test_files: List[TestFileResult]
    distribution: Dict[str, float]      # fraction per type, e.g. {"unit": 0.6, ...}
    counts: Dict[str, int]              # raw count per type
    anti_patterns: List[AntiPatternResult]
    recommendations: List[str]
    ci_pipeline: Optional[CIPipelineInfo] = None

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "repo_path": self.repo_path,
            "timestamp": self.timestamp,
            "total_test_files": self.total_test_files,
            "distribution": {k: round(v, 4) for k, v in self.distribution.items()},
            "counts": self.counts,
            "anti_patterns": [
                {
                    "name": ap.name,
                    "description": ap.description,
                    "detected": ap.detected,
                    "details": ap.details,
                    "severity": ap.severity,
                }
                for ap in self.anti_patterns
            ],
            "recommendations": self.recommendations,
            "test_files": [
                {
                    "path": tf.relative_path,
                    "language": tf.language,
                    "classification": tf.classification,
                    "confidence": round(tf.confidence, 4),
                    "is_ambiguous": tf.is_ambiguous,
                    "scores": {k: round(v, 4) for k, v in tf.scores.items()},
                    "signals": [
                        {
                            "type": s.test_type,
                            "source": s.source,
                            "name": s.name,
                            "weight": s.weight,
                            "matched": s.matched_text,
                        }
                        for s in tf.signals
                    ],
                }
                for tf in self.test_files
            ],
            "ci_pipeline": {
                "source_file": self.ci_pipeline.source_file,
                "tool": self.ci_pipeline.tool,
                "steps": [
                    {
                        "name": s.name,
                        "command": s.command,
                        "test_type_hint": s.test_type_hint,
                    }
                    for s in self.ci_pipeline.steps
                ],
            }
            if self.ci_pipeline
            else None,
        }

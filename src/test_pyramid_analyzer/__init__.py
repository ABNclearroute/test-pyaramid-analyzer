"""test-pyramid-analyzer — deterministic rule-based test pyramid analysis."""

__version__ = "0.1.0"
__author__ = "test-pyramid-analyzer contributors"

from .classifier import TestClassifier
from .models import AnalysisReport, Signal, TestFileResult
from .rules_loader import RulesLoader

__all__ = [
    "__version__",
    "TestClassifier",
    "RulesLoader",
    "AnalysisReport",
    "TestFileResult",
    "Signal",
]

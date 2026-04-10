"""Abstract base class for language detection plugins."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class LanguagePlugin(ABC):
    """Extend this class to add support for a new programming language.

    Plugins are responsible for:
    1. Identifying which files belong to their language.
    2. Extracting language-specific signals (imports, annotations, etc.)
       that the generic regex-based parser cannot easily handle.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique language identifier (e.g. 'python', 'java')."""

    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """File extensions handled by this plugin (lowercase, with dot)."""

    @property
    @abstractmethod
    def test_file_patterns(self) -> List[str]:
        """Glob patterns for test file names (e.g. 'test_*.py')."""

    def extra_signals(
        self, file_path: Path, content: str, rules: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return additional raw signal dicts for a file.

        Each dict must contain: test_type, source, name, weight, matched_text.
        Override in subclasses to add language-specific heuristics beyond what
        the generic rules-based parser already covers.
        """
        return []

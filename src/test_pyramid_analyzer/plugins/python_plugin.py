"""Python language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import LanguagePlugin


class PythonPlugin(LanguagePlugin):
    name = "python"
    extensions = [".py"]
    test_file_patterns = ["test_*.py", "*_test.py"]

    # Decorators / markers that strongly imply test categories
    _INTEGRATION_MARKERS = re.compile(
        r"@pytest\.mark\.integration"
        r"|@pytest\.mark\.django_db"
        r"|@pytest\.mark\.database"
        r"|@pytest\.mark\.external"
    )
    _E2E_MARKERS = re.compile(
        r"@pytest\.mark\.e2e"
        r"|@pytest\.mark\.slow"
        r"|@pytest\.mark\.browser"
        r"|@pytest\.mark\.selenium"
    )
    _UNIT_MARKERS = re.compile(r"@pytest\.mark\.unit")

    def extra_signals(
        self, file_path: Path, content: str, rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if self._UNIT_MARKERS.search(content):
            signals.append(
                {
                    "test_type": "unit",
                    "source": "framework",
                    "name": "pytest.mark.unit",
                    "weight": 3.0,
                    "matched_text": "@pytest.mark.unit",
                }
            )
        if self._INTEGRATION_MARKERS.search(content):
            signals.append(
                {
                    "test_type": "integration",
                    "source": "framework",
                    "name": "pytest.mark.integration/db",
                    "weight": 3.5,
                    "matched_text": self._INTEGRATION_MARKERS.pattern[:40],
                }
            )
        if self._E2E_MARKERS.search(content):
            signals.append(
                {
                    "test_type": "e2e",
                    "source": "framework",
                    "name": "pytest.mark.e2e/browser",
                    "weight": 3.5,
                    "matched_text": self._E2E_MARKERS.pattern[:40],
                }
            )
        return signals

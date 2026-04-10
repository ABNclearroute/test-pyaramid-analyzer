"""Go language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .base import LanguagePlugin


class GoPlugin(LanguagePlugin):
    name = "go"
    extensions = [".go"]
    # Go convention: integration tests live in tests/ dir; all test files end in _test.go
    test_file_patterns = ["*_test.go"]

    # Strong integration signals inside Go test files
    _TESTCONTAINERS = re.compile(r"testcontainers|dockertest|gnomock")
    _INTEGRATION_FUNC = re.compile(r"func Test\w*(Integration|Database|DB|Postgres|MySQL|Redis|Kafka|Queue|HTTP|API|Service)\w*\(")
    _DB_IMPORTS = re.compile(r'"database/sql"|"github\.com/jmoiron/sqlx"|"gorm\.io/gorm"|"github\.com/go-redis/redis"')
    _HTTP_CLIENT = re.compile(r'"net/http/httptest"|"net/http"')

    # E2E signals
    _CHROMEDP = re.compile(r'"github\.com/chromedp/chromedp"')
    _ROD = re.compile(r'"github\.com/go-rod/rod"')
    _PLAYWRIGHT_GO = re.compile(r'"github\.com/playwright-community/playwright-go"')
    _E2E_FUNC = re.compile(r"func Test\w*(E2E|Browser|UI|Acceptance|Selenium)\w*\(")

    # Benchmark → not a test classification signal, skip
    _BENCHMARK = re.compile(r"func Benchmark\w+\(b \*testing\.B\)")

    def extra_signals(self, file_path: Path, content: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals: List[Dict[str, Any]] = []

        if self._CHROMEDP.search(content) or self._ROD.search(content) or self._PLAYWRIGHT_GO.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "go browser automation (chromedp/rod/playwright-go)",
                "weight": 4.5,
                "matched_text": "chromedp / rod / playwright-go import",
            })
        elif self._E2E_FUNC.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "go E2E func naming convention",
                "weight": 3.0,
                "matched_text": self._E2E_FUNC.pattern[:50],
            })

        if self._TESTCONTAINERS.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "testcontainers-go / dockertest",
                "weight": 4.0,
                "matched_text": "testcontainers / dockertest",
            })
        elif self._INTEGRATION_FUNC.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "go integration func naming convention",
                "weight": 2.5,
                "matched_text": self._INTEGRATION_FUNC.pattern[:60],
            })
        elif self._DB_IMPORTS.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "go database import",
                "weight": 2.5,
                "matched_text": "database/sql or gorm import",
            })

        return signals

"""Rust language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import LanguagePlugin


class RustPlugin(LanguagePlugin):
    name = "rust"
    extensions = [".rs"]
    # Unit tests in Rust live in same file with #[cfg(test)];
    # integration tests are in tests/ directory — any .rs file there counts
    test_file_patterns = ["*_test.rs", "test_*.rs", "tests.rs"]

    # Strong unit indicator: inline test module
    _CFG_TEST = re.compile(r"#\[cfg\(test\)\]")
    _UNIT_TEST = re.compile(r"#\[test\]")

    # Integration: async runtime tests, HTTP client, DB drivers
    _TOKIO_TEST = re.compile(r"#\[tokio::test\]")
    _ACTIX_TEST = re.compile(r"actix_web::test|actix_rt::test|test::init_service")
    _AXUM_TEST = re.compile(r"axum_test|axum::Router|tower::ServiceExt")
    _SQLX = re.compile(r"sqlx::test|#\[sqlx::test\]|sqlx::PgPool|sqlx::MySqlPool")
    _REQWEST = re.compile(r"reqwest::|reqwest::blocking")

    # E2E: browser automation
    _FANTOCCINI = re.compile(r"fantoccini::|Client::new")
    _THIRTYFOUR = re.compile(r"thirtyfour::|WebDriver::new")

    def extra_signals(
        self, file_path: Path, content: str, rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if self._FANTOCCINI.search(content) or self._THIRTYFOUR.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "fantoccini / thirtyfour WebDriver",
                "weight": 4.5,
                "matched_text": "fantoccini / thirtyfour WebDriver",
            })

        if (self._SQLX.search(content)
                or self._ACTIX_TEST.search(content)
                or self._AXUM_TEST.search(content)):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "sqlx::test / actix-web test / axum integration",
                "weight": 4.0,
                "matched_text": "sqlx::test / actix_web::test",
            })
        elif self._TOKIO_TEST.search(content) or self._REQWEST.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "tokio::test / reqwest (async integration)",
                "weight": 2.5,
                "matched_text": "#[tokio::test] / reqwest::",
            })

        # Inline unit test module — strong unit signal when in non-tests/ path
        parts = file_path.parts
        in_tests_dir = "tests" in parts
        if not in_tests_dir and (self._CFG_TEST.search(content) or self._UNIT_TEST.search(content)):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "rust #[cfg(test)] inline module",
                "weight": 2.5,
                "matched_text": "#[cfg(test)] / #[test]",
            })

        return signals

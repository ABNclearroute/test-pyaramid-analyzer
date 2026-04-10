"""PHP language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import LanguagePlugin


class PhpPlugin(LanguagePlugin):
    name = "php"
    extensions = [".php"]
    test_file_patterns = [
        "*Test.php",
        "*Tests.php",
        "*Spec.php",
        "test_*.php",
        "*FeatureTest.php",
        "*Feature.php",
        "*Cest.php",         # Codeception Cest
        "*Story.php",        # Behat story
    ]

    # Behat (BDD / E2E)
    _BEHAT = re.compile(r"Behat\\Behat|@Given|@When|@Then|use Behat\\")
    _CODECEPTION_ACCEPTANCE = re.compile(r"AcceptanceTester|extends Cest|WebDriver\s*\$I")

    # Laravel Dusk (E2E browser)
    _DUSK = re.compile(r"Laravel\\Dusk|extends DuskTestCase|DuskBrowser|browse\s*\(function")

    # Integration: database, HTTP client
    _REFRESH_DB = re.compile(r"use RefreshDatabase|use DatabaseMigrations|use DatabaseTransactions")
    _HTTP_TEST = re.compile(r"\$this->get\(|->postJson\(|->assertJson\(|->withHeaders\(")
    _DB_TEST = re.compile(
        r"Illuminate\\Foundation\\Testing\\|PHPUnit\\DbUnit\\|extends DatabaseTestCase"
    )

    # Mockery / prophecy → unit
    _MOCK = re.compile(r"Mockery::|use Prophecy\\|->shouldReceive\(|->willReturn\(")

    def extra_signals(
        self, file_path: Path, content: str, rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if self._BEHAT.search(content) or self._CODECEPTION_ACCEPTANCE.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "Behat BDD / Codeception acceptance",
                "weight": 4.5,
                "matched_text": "Behat / AcceptanceTester",
            })

        if self._DUSK.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "Laravel Dusk (browser)",
                "weight": 5.0,
                "matched_text": "DuskTestCase / browse()",
            })

        if (self._REFRESH_DB.search(content)
                or self._HTTP_TEST.search(content)
                or self._DB_TEST.search(content)):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "Laravel Feature / PHPUnit database test",
                "weight": 3.5,
                "matched_text": "RefreshDatabase / $this->get()",
            })

        if self._MOCK.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "Mockery / Prophecy",
                "weight": 2.5,
                "matched_text": "Mockery:: / shouldReceive()",
            })

        return signals

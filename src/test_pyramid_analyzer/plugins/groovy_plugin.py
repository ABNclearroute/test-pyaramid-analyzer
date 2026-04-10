"""Groovy language plugin (Spock framework, Geb browser automation)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import LanguagePlugin


class GroovyPlugin(LanguagePlugin):
    name = "groovy"
    extensions = [".groovy"]
    test_file_patterns = [
        "*Spec.groovy",
        "*Specification.groovy",
        "*Test.groovy",
        "*Tests.groovy",
        "*IT.groovy",
        "*Feature.groovy",
    ]

    # Spock base classes
    _SPOCK_UNIT = re.compile(r"extends Specification|extends spock\.lang\.Specification")
    _SPOCK_INTEGRATION = re.compile(
        r"@SpringBootTest|@ContextConfiguration|@IntegrationTest"
        r"|@DataJpaTest|extends IntegrationSpec"
    )

    # Geb (browser automation on top of Selenium)
    _GEB = re.compile(r"geb\.|extends GebSpec|extends GebReportingSpec|import geb\.")

    # Spock where/given/when/then block (strong Spock indicator)
    _SPOCK_BLOCKS = re.compile(r"\bwhen:\s*$|\bgiven:\s*$|\bthen:\s*$", re.MULTILINE)

    # Testcontainers
    _TESTCONTAINERS = re.compile(r"org\.testcontainers\.|@Testcontainers|@Container")

    def extra_signals(
        self, file_path: Path, content: str, rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if self._GEB.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "Geb (browser automation)",
                "weight": 5.0,
                "matched_text": "GebSpec / geb.Page",
            })

        if self._SPOCK_INTEGRATION.search(content) or self._TESTCONTAINERS.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "Spock integration / Testcontainers",
                "weight": 4.0,
                "matched_text": "@SpringBootTest / @Testcontainers",
            })

        if self._SPOCK_UNIT.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "Spock Specification",
                "weight": 2.5,
                "matched_text": "extends Specification",
            })

        if self._SPOCK_BLOCKS.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "Spock given/when/then blocks",
                "weight": 1.5,
                "matched_text": "given: / when: / then:",
            })

        return signals

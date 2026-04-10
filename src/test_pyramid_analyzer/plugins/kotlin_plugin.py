"""Kotlin language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .base import LanguagePlugin


class KotlinPlugin(LanguagePlugin):
    name = "kotlin"
    extensions = [".kt", ".kts"]
    test_file_patterns = [
        "*Test.kt",
        "*Tests.kt",
        "*Spec.kt",
        "*IT.kt",
        "*ITCase.kt",
    ]

    # Kotest: describes() / should { } / "string" { } DSLs
    _KOTEST_INTEGRATION = re.compile(r"io\.kotest\.extensions\.(spring|testcontainers|ktor)")
    _KOTEST_UNIT = re.compile(r"io\.kotest\.core\.spec|import io\.kotest\.")
    _MOCKK = re.compile(r"import io\.mockk\.|every\s*\{|coEvery\s*\{|verify\s*\{|mockk<|spyk\(|relaxedMockk")

    # Spring / integration
    _SPRING_BOOT = re.compile(r"@SpringBootTest|@DataJpaTest|@WebMvcTest|@DataMongoTest|@RestClientTest")
    _TESTCONTAINERS = re.compile(r"org\.testcontainers\.|@Testcontainers|@Container")
    _KTOR_TEST = re.compile(r"io\.ktor\.server\.testing\.|testApplication\s*\{|withTestApplication")

    # E2E
    _SELENIUM = re.compile(r"import org\.openqa\.selenium")
    _PLAYWRIGHT = re.compile(r"com\.microsoft\.playwright\.|import com\.playwright")

    # IT suffix naming
    _IT_SUFFIX = re.compile(r"(IT|IntegrationTest)$")

    def extra_signals(self, file_path: Path, content: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals: List[Dict[str, Any]] = []

        if self._SELENIUM.search(content) or self._PLAYWRIGHT.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "Selenium / Playwright (Kotlin)",
                "weight": 4.5,
                "matched_text": "org.openqa.selenium / com.microsoft.playwright",
            })

        if self._SPRING_BOOT.search(content) or self._TESTCONTAINERS.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "Spring Boot Test / Testcontainers (Kotlin)",
                "weight": 4.0,
                "matched_text": "@SpringBootTest / @Testcontainers",
            })
        elif self._KTOR_TEST.search(content) or self._KOTEST_INTEGRATION.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "Ktor testApplication / Kotest extensions",
                "weight": 3.5,
                "matched_text": "testApplication { } / kotest-extensions",
            })
        elif self._IT_SUFFIX.search(file_path.stem):
            signals.append({
                "test_type": "integration",
                "source": "path_pattern",
                "name": "kotlin IT naming convention",
                "weight": 2.5,
                "matched_text": file_path.stem,
            })

        if self._MOCKK.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "MockK",
                "weight": 2.5,
                "matched_text": "mockk<> / every { }",
            })
        elif self._KOTEST_UNIT.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "Kotest",
                "weight": 2.0,
                "matched_text": "io.kotest.core.spec",
            })

        return signals

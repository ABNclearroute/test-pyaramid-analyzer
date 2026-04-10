"""C# / .NET language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import LanguagePlugin


class CSharpPlugin(LanguagePlugin):
    name = "csharp"
    extensions = [".cs"]
    test_file_patterns = [
        "*Tests.cs",
        "*Test.cs",
        "*Spec.cs",
        "*Steps.cs",       # SpecFlow step definitions
        "*Fixture.cs",
        "*Integration*.cs",
    ]

    # Integration: ASP.NET Core test host, Testcontainers
    _WEB_APP_FACTORY = re.compile(
        r"WebApplicationFactory|TestServer|IClassFixture<Web|HttpClient\s+_client"
    )
    _TESTCONTAINERS = re.compile(r"Testcontainers\.|DotNet\.Testcontainers\.|using Testcontainers")
    _EF_DB = re.compile(r"InMemoryDatabase|UseInMemoryDatabase|DbContext|SqliteConnection")

    # E2E: Selenium, Playwright, SpecFlow/Reqnroll
    _SELENIUM = re.compile(r"using OpenQA\.Selenium|IWebDriver|ChromeDriver|FirefoxDriver")
    _PLAYWRIGHT = re.compile(
        r"using Microsoft\.Playwright|IPage\s+\w+|IBrowser\s+\w+|IPlaywright"
    )
    _SPECFLOW = re.compile(
        r"using TechTalk\.SpecFlow|using Reqnroll|\[Binding\]|\[Given\]|\[When\]|\[Then\]"
    )

    # Unit-only markers
    _MOCK_FRAMEWORK = re.compile(
        r"using Moq|using NSubstitute|using FakeItEasy|\.Setup\(|\.Returns\(|Substitute\.For<"
    )

    def extra_signals(
        self, file_path: Path, content: str, rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if self._SELENIUM.search(content) or self._PLAYWRIGHT.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "Selenium / Playwright (.NET)",
                "weight": 4.5,
                "matched_text": "IWebDriver / IPage import",
            })

        if self._SPECFLOW.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "SpecFlow / Reqnroll BDD",
                "weight": 3.5,
                "matched_text": "[Given] / [When] / [Then]",
            })

        if self._WEB_APP_FACTORY.search(content) or self._TESTCONTAINERS.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "WebApplicationFactory / Testcontainers.DotNet",
                "weight": 4.0,
                "matched_text": "WebApplicationFactory / Testcontainers",
            })
        elif self._EF_DB.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "EF Core InMemory / SQLite",
                "weight": 2.5,
                "matched_text": "UseInMemoryDatabase / DbContext",
            })

        if self._MOCK_FRAMEWORK.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "Moq / NSubstitute / FakeItEasy",
                "weight": 2.5,
                "matched_text": ".Setup() / .Returns() / Substitute.For<>",
            })

        return signals

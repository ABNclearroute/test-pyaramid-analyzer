"""JavaScript / TypeScript language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .base import LanguagePlugin


class JavaScriptPlugin(LanguagePlugin):
    name = "javascript"
    extensions = [".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"]
    test_file_patterns = [
        "*.test.js",
        "*.spec.js",
        "*.test.ts",
        "*.spec.ts",
        "*.test.jsx",
        "*.spec.jsx",
        "*.test.tsx",
        "*.spec.tsx",
    ]

    # Cypress-specific patterns
    _CYPRESS = re.compile(r"cy\.(visit|get|contains|click|type|intercept)\(")
    # Playwright-specific patterns
    _PLAYWRIGHT = re.compile(r"(page|browser|context)\.(goto|click|fill|screenshot|waitFor)\(")
    # React Testing Library (unit-level)
    _RTL = re.compile(r"(render|screen)\.(getBy|queryBy|findBy|getAllBy)")
    # MSW / nock mocking (integration hint)
    _MOCKING_MIDDLEWARE = re.compile(r"nock\(|msw|rest\.(get|post|put|delete)\(")

    def extra_signals(
        self, file_path: Path, content: str, rules: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        signals: List[Dict[str, Any]] = []

        if self._CYPRESS.search(content):
            signals.append(
                {
                    "test_type": "e2e",
                    "source": "framework",
                    "name": "cypress commands",
                    "weight": 4.5,
                    "matched_text": "cy.visit / cy.get",
                }
            )

        if self._PLAYWRIGHT.search(content):
            signals.append(
                {
                    "test_type": "e2e",
                    "source": "framework",
                    "name": "playwright page interactions",
                    "weight": 4.5,
                    "matched_text": "page.goto / page.click",
                }
            )

        if self._RTL.search(content):
            signals.append(
                {
                    "test_type": "unit",
                    "source": "framework",
                    "name": "react-testing-library",
                    "weight": 2.5,
                    "matched_text": "render / screen queries",
                }
            )

        if self._MOCKING_MIDDLEWARE.search(content):
            signals.append(
                {
                    "test_type": "integration",
                    "source": "framework",
                    "name": "http mocking (nock/msw)",
                    "weight": 2.5,
                    "matched_text": "nock / msw rest handler",
                }
            )

        return signals

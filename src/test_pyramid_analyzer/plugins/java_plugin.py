"""Java language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .base import LanguagePlugin


class JavaPlugin(LanguagePlugin):
    name = "java"
    extensions = [".java"]
    test_file_patterns = ["*Test.java", "*Tests.java", "*IT.java", "*Spec.java", "*ITCase.java"]

    # Spring Boot integration-test annotations
    _SPRING_INTEGRATION = re.compile(
        r"@SpringBootTest"
        r"|@DataJpaTest"
        r"|@WebMvcTest"
        r"|@DataMongoTest"
        r"|@DataRedisTest"
        r"|@JdbcTest"
    )
    # Integration-test naming convention: *IT.java
    _IT_SUFFIX = re.compile(r"(IT|IntegrationTest)$")

    def extra_signals(
        self, file_path: Path, content: str, rules: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        signals: List[Dict[str, Any]] = []

        # Spring Boot slice / integration annotations
        match = self._SPRING_INTEGRATION.search(content)
        if match:
            signals.append(
                {
                    "test_type": "integration",
                    "source": "framework",
                    "name": f"Spring: {match.group()}",
                    "weight": 4.0,
                    "matched_text": match.group(),
                }
            )

        # IT suffix naming convention
        stem = file_path.stem
        if self._IT_SUFFIX.search(stem):
            signals.append(
                {
                    "test_type": "integration",
                    "source": "path_pattern",
                    "name": "java IT naming convention",
                    "weight": 2.5,
                    "matched_text": stem,
                }
            )

        return signals

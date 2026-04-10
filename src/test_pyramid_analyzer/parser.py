"""Signal extractor — pulls classification signals out of test file content."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .models import Signal
from .plugins import get_plugin


class SignalExtractor:
    """Extract weighted signals from a test file using the configured rules.

    Signal sources (applied in order):
    1. **Path patterns** — directory/file path contains keywords like ``/unit/``.
    2. **Framework detection** — imports or annotations reveal testing framework.
    3. **Code patterns** — regex matches inside the file body (mocking, HTTP, etc.).
    4. **Plugin extras** — language-specific heuristics from ``LanguagePlugin.extra_signals``.
    """

    def __init__(self, rules: dict[str, Any]) -> None:
        self._signals_cfg = rules.get("signals", {})

    def extract(self, file_path: Path, language: str, content: str) -> list[Signal]:
        signals: list[Signal] = []
        signals.extend(self._path_signals(file_path))
        signals.extend(self._framework_signals(content, language))
        signals.extend(self._code_pattern_signals(content))
        signals.extend(self._plugin_signals(file_path, language, content))
        return signals

    # ------------------------------------------------------------------
    # Signal sources
    # ------------------------------------------------------------------

    def _path_signals(self, path: Path) -> list[Signal]:
        """Match path/directory keywords against the configured path_patterns."""
        signals: list[Signal] = []
        path_str = str(path).replace("\\", "/").lower()
        for test_type, entries in self._signals_cfg.get("path_patterns", {}).items():
            for entry in entries:
                keyword = entry["pattern"].lower()
                # Match as a path component segment to avoid false positives
                if re.search(r"(^|/)" + re.escape(keyword.strip("/")) + r"(/|$)", path_str):
                    signals.append(
                        Signal(
                            test_type=test_type,
                            source="path_pattern",
                            name=entry["pattern"],
                            weight=float(entry["weight"]),
                            matched_text=entry["pattern"],
                        )
                    )
        return signals

    def _framework_signals(self, content: str, language: str) -> list[Signal]:
        """Detect testing frameworks by scanning imports and annotations."""
        signals: list[Signal] = []
        for test_type, framework_list in self._signals_cfg.get("frameworks", {}).items():
            for fw in framework_list:
                applicable_langs = fw.get("languages", [])
                if applicable_langs and language not in applicable_langs:
                    continue

                # Check import strings (any single hit counts)
                for import_str in fw.get("imports", []):
                    if import_str in content:
                        signals.append(
                            Signal(
                                test_type=test_type,
                                source="framework",
                                name=fw["name"],
                                weight=float(fw["weight"]),
                                matched_text=import_str,
                            )
                        )
                        break  # one hit per framework is enough

                # Check annotation / keyword patterns
                for raw_pat in fw.get("patterns", []):
                    if re.search(raw_pat, content):
                        signals.append(
                            Signal(
                                test_type=test_type,
                                source="framework",
                                name=fw["name"],
                                weight=float(fw["weight"]),
                                matched_text=raw_pat[:60],
                            )
                        )
                        break

        return signals

    def _code_pattern_signals(self, content: str) -> list[Signal]:
        """Match code-level patterns (mocking, HTTP calls, browser commands, etc.)."""
        signals: list[Signal] = []
        for test_type, patterns in self._signals_cfg.get("code_patterns", {}).items():
            for entry in patterns:
                try:
                    hits = re.findall(entry["pattern"], content)
                except re.error:
                    continue
                if hits:
                    # Cap multiplier at 3 so a single noisy pattern can't dominate
                    multiplier = min(len(hits), 3)
                    signals.append(
                        Signal(
                            test_type=test_type,
                            source="code_pattern",
                            name=entry.get("name", entry["pattern"][:40]),
                            weight=float(entry["weight"]) * multiplier,
                            matched_text=str(hits[:3]),
                        )
                    )
        return signals

    def _plugin_signals(self, file_path: Path, language: str, content: str) -> list[Signal]:
        """Delegate to the registered language plugin for extra heuristics."""
        plugin = get_plugin(language)
        if plugin is None:
            return []
        raw = plugin.extra_signals(file_path, content, self._signals_cfg)
        return [
            Signal(
                test_type=d["test_type"],
                source=d.get("source", "framework"),
                name=d["name"],
                weight=float(d["weight"]),
                matched_text=d.get("matched_text", ""),
            )
            for d in raw
        ]

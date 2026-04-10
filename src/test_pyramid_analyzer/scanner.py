"""Repository scanner — locates test files across a directory tree."""
from __future__ import annotations

import fnmatch
from collections.abc import Iterator
from pathlib import Path

from .plugins import all_plugins
from .plugins.base import LanguagePlugin

# Directories we always skip
_PRUNE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "__pycache__",
        ".tox",
        ".nox",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        ".eggs",
        "target",         # Maven / Gradle
        ".gradle",
        ".idea",
        ".vscode",
        "coverage",
        ".nyc_output",
        "htmlcov",
    }
)


class TestFileScanner:
    """Walk a repository directory tree and return test files with their language.

    Language detection uses the registered :class:`LanguagePlugin` instances,
    so adding a new language only requires registering a new plugin.
    """

    def __init__(self, rules: dict, extra_exclude_dirs: list[str] | None = None) -> None:
        self._rules = rules
        self._prune = _PRUNE_DIRS | set(extra_exclude_dirs or [])

        # Build extension → plugin mapping from registered plugins, validated
        # against the rules config.
        self._ext_to_plugin: dict[str, LanguagePlugin] = {}
        self._plugin_patterns: dict[str, list[str]] = {}

        lang_config = rules.get("languages", {})
        for plugin in all_plugins():
            if plugin.name not in lang_config:
                continue
            cfg = lang_config[plugin.name]
            # Rules can override extensions/patterns; plugin provides defaults
            extensions = cfg.get("extensions", plugin.extensions)
            patterns = cfg.get("test_file_patterns", plugin.test_file_patterns)
            self._plugin_patterns[plugin.name] = patterns
            for ext in extensions:
                self._ext_to_plugin[ext.lower()] = plugin

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, repo_path: Path) -> list[tuple[Path, str]]:
        """Return a list of *(absolute_path, language_name)* tuples.

        Only files whose names match the test-file glob patterns for their
        language are returned.
        """
        results: list[tuple[Path, str]] = []
        for file_path in self._walk(repo_path):
            lang = self._detect_language(file_path)
            if lang and self._is_test_file(file_path, lang):
                results.append((file_path, lang))
        return sorted(results, key=lambda t: str(t[0]))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _walk(self, root: Path) -> Iterator[Path]:
        try:
            entries = list(root.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name not in self._prune:
                    yield from self._walk(entry)
            elif entry.is_file():
                yield entry

    def _detect_language(self, path: Path) -> str | None:
        suffix = path.suffix.lower()
        plugin = self._ext_to_plugin.get(suffix)
        return plugin.name if plugin else None

    def _is_test_file(self, path: Path, language: str) -> bool:
        patterns = self._plugin_patterns.get(language, [])
        name = path.name
        return any(fnmatch.fnmatch(name, pat) for pat in patterns)

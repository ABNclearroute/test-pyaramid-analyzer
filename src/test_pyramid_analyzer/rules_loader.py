"""Loads and validates rule configuration from YAML files."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_DEFAULT_RULES_PATH = Path(__file__).parent / "config" / "default_rules.yaml"

_REQUIRED_SECTIONS = ("languages", "signals", "scoring")


class RulesValidationError(Exception):
    pass


class RulesLoader:
    """Load rule configuration from a YAML file.

    Rules files must contain the top-level sections: languages, signals, scoring.
    A custom rules file is *merged on top of* the defaults so callers only need
    to override what differs.
    """

    def __init__(self, custom_path: Optional[Path] = None) -> None:
        self._custom_path = custom_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        """Return merged rules dictionary ready for use by the pipeline."""
        rules = self._load_file(_DEFAULT_RULES_PATH)

        if self._custom_path:
            overrides = self._load_file(self._custom_path)
            rules = self._deep_merge(rules, overrides)

        self._validate(rules)
        return rules

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_file(path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {path}")
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise RulesValidationError(f"Rules file must contain a YAML mapping: {path}")
        return data

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Recursively merge *override* into *base*, returning a new dict."""
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = RulesLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _validate(rules: Dict[str, Any]) -> None:
        missing = [s for s in _REQUIRED_SECTIONS if s not in rules]
        if missing:
            raise RulesValidationError(
                f"Rules file is missing required sections: {', '.join(missing)}"
            )
        # Validate language entries have expected keys
        for lang, cfg in rules.get("languages", {}).items():
            if "extensions" not in cfg:
                raise RulesValidationError(
                    f"Language '{lang}' is missing 'extensions' key"
                )
            if "test_file_patterns" not in cfg:
                raise RulesValidationError(
                    f"Language '{lang}' is missing 'test_file_patterns' key"
                )

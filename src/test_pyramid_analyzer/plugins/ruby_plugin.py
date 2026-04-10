"""Ruby language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .base import LanguagePlugin


class RubyPlugin(LanguagePlugin):
    name = "ruby"
    extensions = [".rb"]
    test_file_patterns = ["*_spec.rb", "*_test.rb", "test_*.rb"]

    # RSpec metadata for Rails test types
    _SYSTEM_SPEC = re.compile(r"type:\s*:system|type:\s*:feature|type:\s*:view")
    _REQUEST_SPEC = re.compile(r"type:\s*:request|type:\s*:routing|type:\s*:api")
    _UNIT_SPEC = re.compile(r"type:\s*:model|type:\s*:helper|type:\s*:mailer|type:\s*:job|type:\s*:service")

    # Capybara / browser-based
    _CAPYBARA = re.compile(r"include Capybara|Capybara\.visit|Capybara::RSpecMatchers|page\.visit|have_content|have_selector")
    _WATIR = re.compile(r"Watir::Browser|require.*watir")

    # Rack-level integration
    _RACK_TEST = re.compile(r"include Rack::Test::Methods|Rack::MockRequest|rack/test")
    _FACTORY = re.compile(r"FactoryBot\.|factory_bot|FactoryGirl\.")

    # Minitest
    _MINITEST_INTEGRATION = re.compile(r"ActionDispatch::IntegrationTest|ActionController::IntegrationTest")

    def extra_signals(self, file_path: Path, content: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals: List[Dict[str, Any]] = []

        # E2E: browser / system specs
        if self._CAPYBARA.search(content) or self._WATIR.search(content) or self._SYSTEM_SPEC.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "capybara / system spec",
                "weight": 4.5,
                "matched_text": "Capybara / Watir / RSpec system spec",
            })

        # Integration: request/routing/api specs, rack-test, database fixtures
        if self._REQUEST_SPEC.search(content) or self._RACK_TEST.search(content) or self._MINITEST_INTEGRATION.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "rspec request/routing spec or rack-test",
                "weight": 3.5,
                "matched_text": "type: :request / rack-test",
            })
        elif self._FACTORY.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "factory_bot (db-backed tests)",
                "weight": 2.0,
                "matched_text": "FactoryBot.",
            })

        # Unit: model/helper/mailer/job specs
        if self._UNIT_SPEC.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "rspec model/helper/mailer/job spec",
                "weight": 3.0,
                "matched_text": "type: :model / :helper / :mailer / :job",
            })

        return signals

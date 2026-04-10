"""Tests for the test file scanner."""
from pathlib import Path

import pytest

from test_pyramid_analyzer.rules_loader import RulesLoader
from test_pyramid_analyzer.scanner import TestFileScanner

FIXTURE_REPO = Path(__file__).parent / "fixtures" / "sample_repo"


@pytest.fixture(scope="module")
def rules():
    return RulesLoader().load()


@pytest.fixture(scope="module")
def scanner(rules):
    return TestFileScanner(rules)


class TestScannerBehaviour:
    def test_finds_python_unit_test(self, scanner):
        results = scanner.scan(FIXTURE_REPO)
        paths = [str(r[0]) for r in results]
        assert any("test_calculator.py" in p for p in paths)

    def test_finds_python_integration_test(self, scanner):
        results = scanner.scan(FIXTURE_REPO)
        paths = [str(r[0]) for r in results]
        assert any("test_db_connection.py" in p for p in paths)

    def test_finds_python_e2e_test(self, scanner):
        results = scanner.scan(FIXTURE_REPO)
        paths = [str(r[0]) for r in results]
        assert any("test_login_flow.py" in p for p in paths)

    def test_language_detected_as_python(self, scanner):
        results = scanner.scan(FIXTURE_REPO)
        langs = {lang for _, lang in results}
        assert "python" in langs

    def test_no_non_test_files_returned(self, scanner):
        results = scanner.scan(FIXTURE_REPO)
        paths = [str(r[0]) for r in results]
        assert not any("ci.yml" in p for p in paths)

    def test_scan_result_is_sorted(self, scanner):
        results = scanner.scan(FIXTURE_REPO)
        paths = [str(r[0]) for r in results]
        assert paths == sorted(paths)

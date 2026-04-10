"""Tests for the CI pipeline parser."""
from pathlib import Path

import pytest

from test_pyramid_analyzer.ci_parser import CIParser

FIXTURE_CI = (
    Path(__file__).parent
    / "fixtures"
    / "sample_repo"
    / ".github"
    / "workflows"
    / "ci.yml"
)


@pytest.fixture
def parser():
    return CIParser()


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    return CIParser().parse_github_actions(FIXTURE_CI)


class TestGitHubActionsParser:
    def test_tool_is_github_actions(self, pipeline):
        assert pipeline.tool == "github_actions"

    def test_steps_are_populated(self, pipeline):
        assert len(pipeline.steps) >= 3

    def test_unit_step_detected(self, pipeline):
        hints = [s.test_type_hint for s in pipeline.steps]
        assert "unit" in hints

    def test_integration_step_detected(self, pipeline):
        hints = [s.test_type_hint for s in pipeline.steps]
        assert "integration" in hints

    def test_e2e_step_detected(self, pipeline):
        hints = [s.test_type_hint for s in pipeline.steps]
        assert "e2e" in hints

    def test_each_step_has_name_and_command(self, pipeline):
        for step in pipeline.steps:
            assert step.name
            assert step.command


class TestCIParserEdgeCases:
    def test_missing_file_returns_empty_pipeline(self, parser, tmp_path):
        fake = tmp_path / "nonexistent.yml"
        result = parser.parse_github_actions(fake)
        assert result.steps == []

    def test_empty_yaml_returns_empty_pipeline(self, parser, tmp_path):
        empty = tmp_path / "empty.yml"
        empty.write_text("name: CI\non: push\njobs: {}\n")
        result = parser.parse_github_actions(empty)
        assert result.steps == []

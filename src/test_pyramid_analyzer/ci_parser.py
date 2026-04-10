"""CI pipeline parser.

Supported platforms
-------------------
* GitHub Actions   (.github/workflows/*.yml)
* GitLab CI        (.gitlab-ci.yml)
* CircleCI         (.circleci/config.yml)
* Azure Pipelines  (azure-pipelines.yml)
* Travis CI        (.travis.yml)
* Bitbucket Pipelines (bitbucket-pipelines.yml)
* Jenkins          (Jenkinsfile)
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .models import CIPipelineInfo, CIStep

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Command-type classifier
# Ordered list of (test_type, regex_pattern) — first match wins.
# ---------------------------------------------------------------------------
_COMMAND_HINTS: List[Tuple[str, str]] = [
    # ── E2E ──────────────────────────────────────────────────────────────
    ("e2e", r"cypress\s+(run|open)"),
    ("e2e", r"npx\s+cypress"),
    ("e2e", r"playwright\s+test"),
    ("e2e", r"npx\s+playwright"),
    ("e2e", r"nightwatch"),
    ("e2e", r"testcafe"),
    ("e2e", r"selenium"),
    ("e2e", r"detox\s+test"),
    ("e2e", r"appium"),
    ("e2e", r"npm\s+run\s+e2e"),
    ("e2e", r"yarn\s+(run\s+)?e2e"),
    ("e2e", r"pnpm\s+run\s+e2e"),
    ("e2e", r"mvn\s+.*verify(?!\s+.*unit)"),
    ("e2e", r"./gradlew\s+.*e2e"),
    ("e2e", r"bundle\s+exec\s+cucumber"),
    ("e2e", r"behat"),
    ("e2e", r"codecept"),
    ("e2e", r"php\s+artisan\s+dusk"),
    ("e2e", r"pytest\s+.*[/\\]e2e"),
    ("e2e", r"pytest\s+.*-m\s+e2e"),
    ("e2e", r"robot\s+--include\s+e2e"),
    ("e2e", r"sbt\s+.*e2e"),
    ("e2e", r"gatling"),
    # ── Integration ──────────────────────────────────────────────────────
    ("integration", r"pytest\s+.*[/\\]integration"),
    ("integration", r"pytest\s+.*-m\s+integration"),
    ("integration", r"mvn\s+.*integration-test"),
    ("integration", r"./gradlew\s+.*integrationTest"),
    ("integration", r"npm\s+run\s+.*integration"),
    ("integration", r"yarn\s+(run\s+)?.*integration"),
    ("integration", r"go\s+test\s+.*integration"),
    ("integration", r"cargo\s+test\s+.*integration"),
    ("integration", r"dotnet\s+test\s+.*[Ii]ntegration"),
    ("integration", r"bundle\s+exec\s+rspec\s+.*integration"),
    ("integration", r"phpunit\s+.*integration"),
    ("integration", r"sbt\s+.*integrationTest"),
    # ── Unit ─────────────────────────────────────────────────────────────
    ("unit", r"pytest\s+.*-m\s+unit"),
    ("unit", r"pytest\s+.*[/\\]unit"),
    ("unit", r"python\s+-m\s+pytest"),
    ("unit", r"python\s+-m\s+unittest"),
    ("unit", r"nosetests"),
    ("unit", r"nose2"),
    ("unit", r"mvn\s+test(?!\s+.*integration)"),
    ("unit", r"./gradlew\s+test(?!\s+.*integration)"),
    ("unit", r"npm\s+test"),
    ("unit", r"yarn\s+test"),
    ("unit", r"pnpm\s+test"),
    ("unit", r"jest(?!\s+.*e2e)"),
    ("unit", r"vitest"),
    ("unit", r"mocha"),
    ("unit", r"jasmine"),
    ("unit", r"karma"),
    ("unit", r"go\s+test\s+\./\.\.\."),
    ("unit", r"go\s+test\s+\./"),
    ("unit", r"gotestsum"),
    ("unit", r"cargo\s+test"),
    ("unit", r"cargo\s+nextest\s+run"),
    ("unit", r"dotnet\s+test"),
    ("unit", r"bundle\s+exec\s+rspec(?!\s+.*integration)"),
    ("unit", r"bundle\s+exec\s+rake\s+test"),
    ("unit", r"rails\s+test"),
    ("unit", r"phpunit(?!\s+.*integration)"),
    ("unit", r"./vendor/bin/phpunit"),
    ("unit", r"vendor/bin/phpunit"),
    ("unit", r"sbt\s+test(?!\s+.*integration)"),
    ("unit", r"scala\s+test"),
    ("unit", r"make\s+test"),
    ("unit", r"ctest"),
]

# Keywords that flag a step as test-related even without a matched command
_TEST_KEYWORDS = re.compile(
    r"\btest\b|\bspec\b|\be2e\b|\bcoverage\b|\bpytest\b|\bjest\b|\bvitest\b"
    r"|\bcypress\b|\bplaywright\b|\bmocha\b|\bkarma\b|\bjasmine\b|\brspec\b"
    r"|\bphpunit\b|\bbehat\b|\bgotest\b|\bcargo\s+test\b|\bctest\b"
    r"|\bscalatest\b|\bspock\b|\bgeb\b|\bgotestsum\b",
    re.IGNORECASE,
)

# GitLab CI reserved top-level keys (not job names)
_GITLAB_RESERVED = frozenset({
    "stages", "variables", "default", "include", "workflow", "image",
    "services", "cache", "before_script", "after_script",
})


class CIParser:
    """Parse CI pipeline configuration files from multiple platforms."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, pipeline_path: Path) -> CIPipelineInfo:
        """Auto-detect the CI platform and parse the file."""
        tool = self._detect_tool(pipeline_path)
        method = getattr(self, f"_parse_{tool}", None)
        if method is None:
            logger.warning("No dedicated parser for tool '%s', falling back to generic YAML", tool)
            method = self._parse_github_actions  # best-effort generic YAML
        logger.debug("Parsing %s as %s", pipeline_path, tool)
        return method(pipeline_path)

    # Convenience wrappers kept for backward compatibility / direct use
    def parse_github_actions(self, path: Path) -> CIPipelineInfo:
        return self._parse_github_actions(path)

    def parse_gitlab_ci(self, path: Path) -> CIPipelineInfo:
        return self._parse_gitlab_ci(path)

    def parse_circleci(self, path: Path) -> CIPipelineInfo:
        return self._parse_circleci(path)

    def parse_azure_pipelines(self, path: Path) -> CIPipelineInfo:
        return self._parse_azure_pipelines(path)

    def parse_travis_ci(self, path: Path) -> CIPipelineInfo:
        return self._parse_travis_ci(path)

    def parse_bitbucket_pipelines(self, path: Path) -> CIPipelineInfo:
        return self._parse_bitbucket_pipelines(path)

    def parse_jenkins(self, path: Path) -> CIPipelineInfo:
        return self._parse_jenkins(path)

    # ------------------------------------------------------------------
    # Platform detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_tool(path: Path) -> str:
        name = path.name.lower()
        parts = [p.lower() for p in path.parts]

        if ".github" in parts and "workflows" in parts:
            return "github_actions"
        if name in (".gitlab-ci.yml", ".gitlab-ci.yaml"):
            return "gitlab_ci"
        if ".circleci" in parts and "config" in name:
            return "circleci"
        if name in ("azure-pipelines.yml", "azure-pipelines.yaml"):
            return "azure_pipelines"
        if name in (".travis.yml", ".travis.yaml", "travis.yml"):
            return "travis_ci"
        if name == "bitbucket-pipelines.yml":
            return "bitbucket_pipelines"
        if "jenkinsfile" in name:
            return "jenkins"
        return "github_actions"

    # ------------------------------------------------------------------
    # GitHub Actions
    # ------------------------------------------------------------------

    def _parse_github_actions(self, path: Path) -> CIPipelineInfo:
        config = self._load_yaml(path)
        if not config:
            return CIPipelineInfo(source_file=str(path), tool="github_actions")

        steps: List[CIStep] = []
        for _job_name, job in (config.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                run_cmd: str = step.get("run", "") or ""
                if not run_cmd:
                    continue
                name = step.get("name", "") or run_cmd.split("\n")[0][:80]
                hint = self._classify_command(run_cmd)
                if hint is not None or _TEST_KEYWORDS.search(run_cmd):
                    steps.append(CIStep(
                        name=name.strip(),
                        command=run_cmd.strip(),
                        test_type_hint=hint,
                    ))
        return CIPipelineInfo(source_file=str(path), tool="github_actions", steps=steps)

    # ------------------------------------------------------------------
    # GitLab CI
    # ------------------------------------------------------------------

    def _parse_gitlab_ci(self, path: Path) -> CIPipelineInfo:
        config = self._load_yaml(path)
        if not config:
            return CIPipelineInfo(source_file=str(path), tool="gitlab_ci")

        steps: List[CIStep] = []
        for job_name, job in config.items():
            if job_name.startswith(".") or job_name in _GITLAB_RESERVED:
                continue
            if not isinstance(job, dict):
                continue
            for cmd in self._flatten_script(job.get("script")):
                hint = self._classify_command(cmd)
                if hint is not None or _TEST_KEYWORDS.search(cmd):
                    steps.append(CIStep(
                        name=job_name,
                        command=cmd.strip(),
                        test_type_hint=hint,
                    ))
        return CIPipelineInfo(source_file=str(path), tool="gitlab_ci", steps=steps)

    # ------------------------------------------------------------------
    # CircleCI
    # ------------------------------------------------------------------

    def _parse_circleci(self, path: Path) -> CIPipelineInfo:
        config = self._load_yaml(path)
        if not config:
            return CIPipelineInfo(source_file=str(path), tool="circleci")

        steps: List[CIStep] = []
        # Handles both config v2 (jobs map) and v2.1 (orbs / commands)
        for job_name, job in (config.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                cmd, name = self._extract_circleci_step(step, job_name)
                if cmd:
                    hint = self._classify_command(cmd)
                    if hint is not None or _TEST_KEYWORDS.search(cmd):
                        steps.append(CIStep(
                            name=name,
                            command=cmd.strip(),
                            test_type_hint=hint,
                        ))
        return CIPipelineInfo(source_file=str(path), tool="circleci", steps=steps)

    @staticmethod
    def _extract_circleci_step(step: Any, default_name: str) -> Tuple[str, str]:
        if isinstance(step, str):
            return "", default_name
        if not isinstance(step, dict):
            return "", default_name
        run = step.get("run")
        if run is None:
            return "", default_name
        if isinstance(run, str):
            return run, default_name
        if isinstance(run, dict):
            return run.get("command", ""), run.get("name", default_name)
        return "", default_name

    # ------------------------------------------------------------------
    # Azure Pipelines
    # ------------------------------------------------------------------

    def _parse_azure_pipelines(self, path: Path) -> CIPipelineInfo:
        config = self._load_yaml(path)
        if not config:
            return CIPipelineInfo(source_file=str(path), tool="azure_pipelines")

        raw_steps: List[dict] = []
        # Collect steps from nested stages → jobs → steps, or flat
        if "stages" in config:
            for stage in config.get("stages") or []:
                for job in (stage.get("jobs") or []):
                    raw_steps.extend(job.get("steps") or [])
        elif "jobs" in config:
            for job in config.get("jobs") or []:
                raw_steps.extend(job.get("steps") or [])
        else:
            raw_steps = config.get("steps") or []

        steps: List[CIStep] = []
        for step in raw_steps:
            if not isinstance(step, dict):
                continue
            # Azure Pipelines uses 'script', 'bash', 'pwsh', 'powershell'
            cmd = (step.get("script") or step.get("bash")
                   or step.get("pwsh") or step.get("powershell") or "")
            if not cmd:
                continue
            name = step.get("displayName") or step.get("name") or cmd.split("\n")[0][:60]
            hint = self._classify_command(cmd)
            if hint is not None or _TEST_KEYWORDS.search(cmd):
                steps.append(CIStep(
                    name=name.strip(),
                    command=cmd.strip(),
                    test_type_hint=hint,
                ))
        return CIPipelineInfo(source_file=str(path), tool="azure_pipelines", steps=steps)

    # ------------------------------------------------------------------
    # Travis CI
    # ------------------------------------------------------------------

    def _parse_travis_ci(self, path: Path) -> CIPipelineInfo:
        config = self._load_yaml(path)
        if not config:
            return CIPipelineInfo(source_file=str(path), tool="travis_ci")

        steps: List[CIStep] = []
        # Travis uses 'script', 'before_script', 'after_success'
        for section in ("before_script", "script", "after_success"):
            for cmd in self._flatten_script(config.get(section)):
                hint = self._classify_command(cmd)
                if hint is not None or _TEST_KEYWORDS.search(cmd):
                    steps.append(CIStep(
                        name=f"{section}: {cmd[:50]}",
                        command=cmd.strip(),
                        test_type_hint=hint,
                    ))
        return CIPipelineInfo(source_file=str(path), tool="travis_ci", steps=steps)

    # ------------------------------------------------------------------
    # Bitbucket Pipelines
    # ------------------------------------------------------------------

    def _parse_bitbucket_pipelines(self, path: Path) -> CIPipelineInfo:
        config = self._load_yaml(path)
        if not config:
            return CIPipelineInfo(source_file=str(path), tool="bitbucket_pipelines")

        steps: List[CIStep] = []
        for pipeline_name, pipeline_entries in (config.get("pipelines") or {}).items():
            if not isinstance(pipeline_entries, list):
                continue
            for entry in pipeline_entries:
                if not isinstance(entry, dict):
                    continue
                # Entry can be {step: {...}} or {parallel: [{step: {...}}, ...]}
                step_dicts = [entry.get("step")]
                if "parallel" in entry:
                    step_dicts = [p.get("step") for p in (entry.get("parallel") or [])]

                for step_dict in step_dicts:
                    if not isinstance(step_dict, dict):
                        continue
                    step_name = step_dict.get("name", pipeline_name)
                    for cmd in self._flatten_script(step_dict.get("script")):
                        hint = self._classify_command(cmd)
                        if hint is not None or _TEST_KEYWORDS.search(cmd):
                            steps.append(CIStep(
                                name=step_name,
                                command=cmd.strip(),
                                test_type_hint=hint,
                            ))
        return CIPipelineInfo(source_file=str(path), tool="bitbucket_pipelines", steps=steps)

    # ------------------------------------------------------------------
    # Jenkins (Declarative / Scripted Groovy DSL)
    # ------------------------------------------------------------------

    def _parse_jenkins(self, path: Path) -> CIPipelineInfo:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.error("Cannot read Jenkinsfile %s: %s", path, exc)
            return CIPipelineInfo(source_file=str(path), tool="jenkins")

        steps: List[CIStep] = []

        # Declarative: stage('Name') { steps { sh '...' } }
        stage_pattern = re.compile(
            r"stage\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
            re.DOTALL,
        )
        sh_pattern = re.compile(r"\bsh\s+['\"]([^'\"]+)['\"]")

        for stage_match in stage_pattern.finditer(content):
            stage_name = stage_match.group(1)
            stage_body = stage_match.group(2)
            for sh_match in sh_pattern.finditer(stage_body):
                cmd = sh_match.group(1)
                hint = self._classify_command(cmd)
                if hint is not None or _TEST_KEYWORDS.search(cmd):
                    steps.append(CIStep(
                        name=stage_name,
                        command=cmd.strip(),
                        test_type_hint=hint,
                    ))

        # Scripted: bare sh '...' outside stage blocks (fallback)
        if not steps:
            for sh_match in sh_pattern.finditer(content):
                cmd = sh_match.group(1)
                hint = self._classify_command(cmd)
                if hint is not None or _TEST_KEYWORDS.search(cmd):
                    steps.append(CIStep(
                        name="Jenkinsfile",
                        command=cmd.strip(),
                        test_type_hint=hint,
                    ))

        return CIPipelineInfo(source_file=str(path), tool="jenkins", steps=steps)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_yaml(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            with path.open(encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            return data if isinstance(data, dict) else None
        except (OSError, yaml.YAMLError) as exc:
            logger.error("Failed to parse %s: %s", path, exc)
            return None

    @staticmethod
    def _flatten_script(value: Any) -> List[str]:
        """Return a flat list of command strings from a scalar, list, or None."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            result = []
            for item in value:
                if isinstance(item, str):
                    result.append(item)
            return result
        return []

    @staticmethod
    def _classify_command(command: str) -> Optional[str]:
        """Return the test type hint for a shell command string, or None."""
        for test_type, pattern in _COMMAND_HINTS:
            if re.search(pattern, command, re.IGNORECASE):
                return test_type
        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def infer_pipeline_tool(path: Path) -> str:
        """Guess the CI platform from the file path (public utility)."""
        return CIParser._detect_tool(path)

"""CLI entry-point for test-pyramid-analyzer.

Commands
--------
  tpa scan <repo>              — analyse a repository
  tpa ci   <pipeline_file>     — parse and display a CI pipeline

Options
-------
  --config PATH      custom rules YAML (merged on top of defaults)
  --output FORMAT    console | json | html  (default: console)
  --out-file PATH    write output to file instead of stdout
  --debug            print per-file scoring details
  --exclude DIRS     comma-separated extra directory names to skip
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from .anti_patterns import AntiPatternDetector, generate_recommendations
from .ci_parser import CIParser
from .classifier import TestClassifier
from .report_generator import ReportGenerator
from .rules_loader import RulesLoader

app = typer.Typer(
    name="tpa",
    help="Test Pyramid Analyzer — deterministic rule-based test classification.",
    add_completion=False,
    rich_markup_mode="rich",
)

_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s  %(name)s  %(message)s",
        level=level,
        stream=sys.stderr,
    )


def _load_rules(config: Optional[Path]) -> dict:
    try:
        return RulesLoader(custom_path=config).load()
    except FileNotFoundError as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc
    except Exception as exc:  # noqa: BLE001
        _console.print(f"[red]Failed to load rules:[/red] {exc}")
        raise typer.Exit(1) from exc


def _output_option() -> typer.Option:
    return typer.Option("console", "--output", "-o", help="Output format: console | json | html")


# ---------------------------------------------------------------------------
# scan command
# ---------------------------------------------------------------------------

@app.command()
def scan(
    repo_path: Path = typer.Argument(..., help="Path to the repository to analyse."),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to a custom rules YAML file."
    ),
    output: str = typer.Option(
        "console", "--output", "-o", help="Output format: console | json | html"
    ),
    out_file: Optional[Path] = typer.Option(
        None, "--out-file", "-f", help="Write report to this file."
    ),
    ci_file: Optional[Path] = typer.Option(
        None, "--ci", help="CI pipeline file to include in the report (e.g. .github/workflows/ci.yml)."
    ),
    exclude: Optional[str] = typer.Option(
        None, "--exclude", help="Comma-separated directory names to skip (e.g. 'vendor,third_party')."
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Print per-file scoring details."),
) -> None:
    """Scan a repository and report the test pyramid distribution."""
    _setup_logging(debug)

    if not repo_path.is_dir():
        _console.print(f"[red]Error:[/red] '{repo_path}' is not a directory.")
        raise typer.Exit(1)

    rules = _load_rules(config)

    # Optional extra excludes
    extra_excludes: List[str] = []
    if exclude:
        extra_excludes = [d.strip() for d in exclude.split(",") if d.strip()]

    # Inject extra excludes into scanner config (scanner reads them from rules)
    if extra_excludes:
        rules.setdefault("scanner", {})["extra_exclude_dirs"] = extra_excludes

    classifier = TestClassifier(rules, debug=debug)

    # ── CI pipeline (optional) ─────────────────────────────────────────
    ci_info = None
    if ci_file:
        if not ci_file.exists():
            _console.print(f"[yellow]Warning:[/yellow] CI file '{ci_file}' not found — skipping.")
        else:
            try:
                ci_info = CIParser().parse(ci_file)
            except Exception as exc:  # noqa: BLE001
                _console.print(f"[yellow]Warning:[/yellow] Could not parse CI file: {exc}")
    else:
        # Auto-detect common CI files inside the repo
        ci_info = _auto_detect_ci(repo_path)

    # ── Classify (single pass) ─────────────────────────────────────────
    try:
        test_files = classifier.classify_files(repo_path)
    except Exception as exc:  # noqa: BLE001
        _console.print(f"[red]Analysis failed:[/red] {exc}")
        if debug:
            import traceback; traceback.print_exc()
        raise typer.Exit(1) from exc

    # ── Aggregate ─────────────────────────────────────────────────────
    distribution, counts = TestClassifier._aggregate(test_files)

    # ── Anti-patterns + recommendations ───────────────────────────────
    detector = AntiPatternDetector()
    anti_patterns = detector.detect(distribution)
    recommendations = generate_recommendations(distribution, anti_patterns)

    # ── Assemble report without re-classifying ─────────────────────────
    from datetime import datetime, timezone
    from .models import AnalysisReport

    report = AnalysisReport(
        repo_path=str(repo_path.resolve()),
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        total_test_files=len(test_files),
        test_files=test_files,
        distribution=distribution,
        counts=counts,
        anti_patterns=anti_patterns,
        recommendations=recommendations,
        ci_pipeline=ci_info,
    )

    # ── Output ────────────────────────────────────────────────────────
    generator = ReportGenerator()
    try:
        generator.generate(report, output_format=output, output_file=out_file, debug=debug)
    except Exception as exc:  # noqa: BLE001
        _console.print(f"[red]Report generation failed:[/red] {exc}")
        raise typer.Exit(1) from exc


# ---------------------------------------------------------------------------
# ci command
# ---------------------------------------------------------------------------

@app.command()
def ci(
    pipeline_file: Path = typer.Argument(..., help="Path to the CI pipeline file."),
    output: str = typer.Option(
        "console", "--output", "-o", help="Output format: console | json"
    ),
    out_file: Optional[Path] = typer.Option(
        None, "--out-file", "-f", help="Write output to this file."
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Verbose output."),
) -> None:
    """Parse a CI pipeline file and display detected test steps."""
    _setup_logging(debug)

    if not pipeline_file.exists():
        _console.print(f"[red]Error:[/red] '{pipeline_file}' not found.")
        raise typer.Exit(1)

    try:
        info = CIParser().parse(pipeline_file)
    except Exception as exc:  # noqa: BLE001
        _console.print(f"[red]Failed to parse pipeline:[/red] {exc}")
        raise typer.Exit(1) from exc

    if output == "json":
        import json
        payload = {
            "source_file": info.source_file,
            "tool": info.tool,
            "steps": [
                {"name": s.name, "command": s.command, "test_type_hint": s.test_type_hint}
                for s in info.steps
            ],
        }
        text = json.dumps(payload, indent=2)
        if out_file:
            out_file.write_text(text)
            _console.print(f"[green]Written to {out_file}[/green]")
        else:
            print(text)
        return

    # Console output
    from rich.table import Table
    from rich import box

    console = Console()
    console.print()
    console.print(f"[bold cyan]CI Pipeline[/bold cyan] — {info.tool.replace('_', ' ').title()}")
    console.print(f"[dim]{info.source_file}[/dim]")
    console.print()

    if not info.steps:
        console.print("[yellow]No test steps found in this pipeline file.[/yellow]")
        return

    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Step", max_width=40)
    table.add_column("Command", max_width=60)
    table.add_column("Test Type")

    type_styles = {"unit": "green", "integration": "yellow", "e2e": "red"}
    for step in info.steps:
        color = type_styles.get(step.test_type_hint or "", "dim")
        from rich.text import Text
        table.add_row(
            step.name[:40],
            step.command.split("\n")[0][:60],
            Text(step.test_type_hint or "unknown", style=color),
        )
    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# version command
# ---------------------------------------------------------------------------

@app.command()
def version() -> None:
    """Print the installed version."""
    from . import __version__
    typer.echo(f"test-pyramid-analyzer {__version__}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CI_CANDIDATES = [
    # GitHub Actions (scan common workflow names)
    ".github/workflows/ci.yml",
    ".github/workflows/ci.yaml",
    ".github/workflows/test.yml",
    ".github/workflows/test.yaml",
    ".github/workflows/tests.yml",
    ".github/workflows/tests.yaml",
    ".github/workflows/build.yml",
    ".github/workflows/build.yaml",
    ".github/workflows/main.yml",
    ".github/workflows/pipeline.yml",
    ".github/workflows/checks.yml",
    # GitLab CI
    ".gitlab-ci.yml",
    ".gitlab-ci.yaml",
    # CircleCI
    ".circleci/config.yml",
    ".circleci/config.yaml",
    # Azure Pipelines
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
    # Travis CI
    ".travis.yml",
    ".travis.yaml",
    # Bitbucket Pipelines
    "bitbucket-pipelines.yml",
    # Jenkins
    "Jenkinsfile",
    "jenkins/Jenkinsfile",
    "ci/Jenkinsfile",
]


def _auto_detect_ci(repo_path: Path):
    """Try each known CI file location and return the first successfully parsed pipeline."""
    parser = CIParser()
    # GitHub Actions: scan all files in .github/workflows/
    workflows_dir = repo_path / ".github" / "workflows"
    if workflows_dir.is_dir():
        for yml in sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml")):
            try:
                info = parser.parse(yml)
                if info.steps:
                    return info
            except Exception:  # noqa: BLE001
                pass

    for rel in _CI_CANDIDATES:
        if ".github/workflows" in rel:
            continue  # already handled above
        candidate = repo_path / rel
        if candidate.exists():
            try:
                return parser.parse(candidate)
            except Exception:  # noqa: BLE001
                pass
    return None


if __name__ == "__main__":
    app()

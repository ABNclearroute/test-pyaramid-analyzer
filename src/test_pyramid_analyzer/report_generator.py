"""Report generators: console (Rich), JSON, and HTML (Jinja2)."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import AnalysisReport

logger = logging.getLogger(__name__)

_CONSOLE = Console()

_TYPE_STYLES: dict = {
    "unit": "bold green",
    "integration": "bold yellow",
    "e2e": "bold red",
    "ambiguous": "bold blue",
    "unknown": "dim",
}

_SEVERITY_STYLES: dict = {
    "error": "bold red",
    "warning": "yellow",
}


class ReportGenerator:
    """Generate analysis reports in the requested format.

    Supported *output_format* values: ``"console"``, ``"json"``, ``"html"``.
    """

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or _CONSOLE

    # ------------------------------------------------------------------
    # Public dispatch
    # ------------------------------------------------------------------

    def generate(
        self,
        report: AnalysisReport,
        output_format: str,
        output_file: Path | None = None,
        debug: bool = False,
    ) -> None:
        fmt = output_format.lower()
        if fmt == "console":
            self._console_report(report, debug=debug)
        elif fmt == "json":
            self._json_report(report, output_file)
        elif fmt == "html":
            self._html_report(report, output_file)
        else:
            raise ValueError(f"Unknown output format '{fmt}'. Choose: console | json | html")

    # ------------------------------------------------------------------
    # Console report (Rich)
    # ------------------------------------------------------------------

    def _console_report(self, report: AnalysisReport, debug: bool = False) -> None:
        c = self._console

        c.print()
        c.print(
            Panel.fit(
                f"[bold cyan]Test Pyramid Analyzer[/bold cyan]\n"
                f"[dim]Repo:[/dim] [white]{report.repo_path}[/white]\n"
                f"[dim]Scanned:[/dim] [white]{report.timestamp}[/white]",
                border_style="cyan",
                padding=(0, 2),
            )
        )

        # ── Distribution ──────────────────────────────────────────────
        dist_table = Table(
            title="Test Distribution",
            box=box.ROUNDED,
            border_style="cyan",
            show_footer=True,
        )
        dist_table.add_column("Type", footer="[bold]Total[/bold]")
        dist_table.add_column(
            "Count", justify="right",
            footer=f"[bold]{report.total_test_files}[/bold]",
        )
        dist_table.add_column("Share", justify="right")
        dist_table.add_column("Distribution", width=32)

        for test_type in ("unit", "integration", "e2e", "ambiguous", "unknown"):
            count = report.counts.get(test_type, 0)
            pct = report.distribution.get(test_type, 0.0)
            style = _TYPE_STYLES.get(test_type, "white")
            filled = int(round(pct * 30))
            bar = Text("█" * filled + "░" * (30 - filled), style=style)
            dist_table.add_row(
                Text(test_type.title(), style=style),
                str(count),
                f"{pct:.1%}",
                bar,
            )
        c.print(dist_table)

        # ── Anti-patterns ──────────────────────────────────────────────
        c.print()
        ap_table = Table(title="Anti-Pattern Check", box=box.ROUNDED, border_style="yellow")
        ap_table.add_column("Pattern", style="bold")
        ap_table.add_column("Status", justify="center")
        ap_table.add_column("Details")

        any_detected = False
        for ap in report.anti_patterns:
            if ap.detected:
                any_detected = True
                sev_style = _SEVERITY_STYLES.get(ap.severity, "yellow")
                status = Text("● DETECTED", style=sev_style)
            else:
                status = Text("✓ OK", style="green")
            ap_table.add_row(ap.name, status, ap.details or ap.description)
        c.print(ap_table)

        if not any_detected:
            c.print("[green]No anti-patterns detected.[/green]")

        # ── Recommendations ────────────────────────────────────────────
        if report.recommendations:
            c.print()
            c.print("[bold]Recommendations[/bold]")
            for i, rec in enumerate(report.recommendations, 1):
                c.print(f"  [cyan]{i:>2}.[/cyan] {rec}")

        # ── CI Pipeline ────────────────────────────────────────────────
        if report.ci_pipeline and report.ci_pipeline.steps:
            c.print()
            ci_table = Table(
                title=f"CI Pipeline — {report.ci_pipeline.tool.replace('_', ' ').title()}",
                box=box.ROUNDED,
            )
            ci_table.add_column("Step", max_width=40)
            ci_table.add_column("Command", max_width=55)
            ci_table.add_column("Hint")
            for step in report.ci_pipeline.steps:
                hint_style = _TYPE_STYLES.get(step.test_type_hint or "", "dim")
                ci_table.add_row(
                    step.name[:40],
                    step.command.split("\n")[0][:55],
                    Text(step.test_type_hint or "–", style=hint_style),
                )
            c.print(ci_table)

        # ── Debug: per-file explain mode ──────────────────────────────
        if debug and report.test_files:
            from .debug_printer import DebugPrinter
            DebugPrinter(c).print_report(report)

        c.print()

    # ------------------------------------------------------------------
    # JSON report
    # ------------------------------------------------------------------

    def _json_report(self, report: AnalysisReport, output_file: Path | None) -> None:
        payload = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        if output_file:
            output_file.write_text(payload, encoding="utf-8")
            self._console.print(f"[green]JSON report written to[/green] {output_file}")
        else:
            print(payload)

    # ------------------------------------------------------------------
    # HTML report (Jinja2)
    # ------------------------------------------------------------------

    def _html_report(self, report: AnalysisReport, output_file: Path | None) -> None:
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
        except ImportError:
            raise RuntimeError("Jinja2 is required for HTML reports: pip install jinja2")

        templates_dir = Path(__file__).parent / "templates"
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "j2"]),
        )

        # Inject helpers for the template
        env.filters["pct"] = lambda v: f"{v:.1%}"
        env.filters["round2"] = lambda v: round(v, 2)

        template = env.get_template("report.html.j2")
        html = template.render(report=report, data=report.to_dict())

        dest = output_file or Path("test_pyramid_report.html")
        dest.write_text(html, encoding="utf-8")
        self._console.print(f"[green]HTML report written to[/green] {dest}")

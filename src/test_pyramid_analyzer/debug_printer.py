"""Explain-mode (--debug) printer for test-pyramid-analyzer.

Produces a rich, human-readable breakdown for every classified test file:

    Test: tests/login.spec.js  [javascript]
    ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

    Signals Detected  (3 signals)
    ┌─────────────┬───────────────┬────────────────────┬────────┬──────────────┐
    │ Source      │ Signal        │ Matched            │ Weight │ → Type       │
    ├─────────────┼───────────────┼────────────────────┼────────┼──────────────┤
    │ framework   │ Playwright    │ import playwright  │  +5.0  │ e2e          │
    │ code_pattern│ page.goto     │ page.goto(         │  +5.0  │ e2e          │
    │ code_pattern│ click()       │ .click()           │  +3.0  │ e2e          │
    └─────────────┴───────────────┴────────────────────┴────────┴──────────────┘

    Score Breakdown
    Unit           ░░░░░░░░░░░░░░░░░░░░░░░░   0.0
    Integration    ░░░░░░░░░░░░░░░░░░░░░░░░   0.0
    E2E            ████████████████████████  13.0  ←

    → E2E  confidence: 0.87  ██████████████████░░

Public API
----------
    DebugPrinter(console).print_report(report)     — all files
    DebugPrinter(console).print_file(result)        — single file
"""
from __future__ import annotations

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .models import AnalysisReport, TestFileResult

# ── Style constants ───────────────────────────────────────────────────────────
_TYPE_STYLE: dict[str, str] = {
    "unit":        "bold green",
    "integration": "bold yellow",
    "e2e":         "bold red",
    "ambiguous":   "bold blue",
    "unknown":     "dim",
}

_SOURCE_LABEL: dict[str, str] = {
    "path_pattern": "path",
    "framework":    "framework",
    "code_pattern": "code",
    "plugin":       "plugin",
}

_BAR_WIDTH  = 24   # width of score bar in characters
_MAX_MATCH  = 32   # truncation limit for matched_text column


def _clean_matched(raw: str) -> str:
    """Return a human-readable snippet from a signal's matched_text.

    The parser sometimes stores ``str(hits[:3])`` which looks like
    ``"['mock', 'patch', ...]"``.  We unwrap that into a clean
    comma-separated string so it reads naturally in the table.
    """
    text = raw.strip()
    if not text:
        return ""
    # Looks like a Python list repr → unwrap
    if text.startswith("[") and text.endswith("]"):
        try:
            import ast
            items = ast.literal_eval(text)
            if isinstance(items, list):
                # Each item may itself be a tuple (from re.findall groups)
                parts: list[str] = []
                for item in items[:3]:
                    if isinstance(item, (list, tuple)):
                        parts.append(", ".join(str(x) for x in item if x))
                    else:
                        parts.append(str(item))
                text = "  ·  ".join(p for p in parts if p)
        except (ValueError, SyntaxError):
            pass
    # Final truncation
    if len(text) > _MAX_MATCH:
        text = text[:_MAX_MATCH - 1] + "…"
    return text


class DebugPrinter:
    """Render per-file classification explanations using Rich."""

    def __init__(self, console: Console | None = None) -> None:
        self._c = console or Console()

    # ── Public API ────────────────────────────────────────────────────────────

    def print_report(self, report: AnalysisReport) -> None:
        """Print explain-mode output for every file in *report*."""
        if not report.test_files:
            self._c.print("[dim]No test files found — nothing to explain.[/dim]")
            return

        self._c.print()
        self._c.print(
            Rule(
                f"[bold cyan]Explain Mode[/bold cyan]  "
                f"[dim]({len(report.test_files)} files)[/dim]",
                style="cyan",
            )
        )

        for result in report.test_files:
            self._c.print()
            self.print_file(result)

        self._c.print()
        self._c.print(Rule(style="cyan"))
        self._print_summary(report)

    def print_file(self, result: TestFileResult) -> None:
        """Print the full explain block for a single :class:`TestFileResult`."""
        self._print_file_header(result)
        self._print_signals_table(result)
        self._print_score_breakdown(result)
        self._print_verdict(result)

    # ── Header ────────────────────────────────────────────────────────────────

    def _print_file_header(self, result: TestFileResult) -> None:
        lang = f"[dim]{result.language}[/dim]"
        path = f"[bold white]{result.relative_path}[/bold white]"
        self._c.print(Rule(f"  {path}  {lang}  ", style="dim", align="left"))

    # ── Signals table ─────────────────────────────────────────────────────────

    def _print_signals_table(self, result: TestFileResult) -> None:
        signals = result.signals

        if not signals:
            self._c.print("  [dim]No signals detected.[/dim]")
            return

        count_str = f"[dim]({len(signals)} signal{'s' if len(signals) != 1 else ''})[/dim]"
        self._c.print(f"  [bold]Signals Detected[/bold]  {count_str}")
        self._c.print()

        tbl = Table(
            box=box.SIMPLE_HEAD,
            show_edge=False,
            pad_edge=True,
            header_style="bold dim",
        )
        tbl.add_column("Source",  style="dim",   width=12, no_wrap=True)
        tbl.add_column("Signal",  max_width=28,  overflow="fold")
        tbl.add_column("Matched", max_width=_MAX_MATCH, style="italic dim")
        tbl.add_column("Weight",  justify="right", width=7)
        tbl.add_column("→ Type",  width=13)

        # Group-sort: signals for the winning type first, then others
        winner = result.classification if not result.is_ambiguous else ""
        sorted_signals = sorted(
            signals,
            key=lambda s: (s.test_type != winner, s.source, -s.weight),
        )

        for sig in sorted_signals:
            type_style = _TYPE_STYLE.get(sig.test_type, "white")
            source_label = _SOURCE_LABEL.get(sig.source, sig.source)
            matched = _clean_matched(sig.matched_text or "")
            weight_str = Text(f"+{sig.weight:.1f}", style="bold")
            type_text  = Text(sig.test_type, style=type_style)

            tbl.add_row(source_label, sig.name, matched, weight_str, type_text)

        self._c.print(tbl)

    # ── Score breakdown ───────────────────────────────────────────────────────

    def _print_score_breakdown(self, result: TestFileResult) -> None:
        scores = result.scores
        total  = sum(scores.values())
        if total == 0:
            return

        self._c.print(f"  [bold]Score Breakdown[/bold]  [dim](total: {total:.1f})[/dim]")
        self._c.print()

        max_score = max(scores.values()) if scores else 1.0

        winner = max(scores, key=lambda k: scores[k]) if scores else None
        for test_type in ("unit", "integration", "e2e"):
            score  = scores.get(test_type, 0.0)
            style  = _TYPE_STYLE.get(test_type, "white")
            filled = int(round((score / max_score) * _BAR_WIDTH)) if max_score else 0
            bar    = Text(
                "█" * filled + "░" * (_BAR_WIDTH - filled),
                style=style if score > 0 else "dim",
            )
            is_winner = test_type == winner and score > 0
            arrow = Text(" ←", style=f"bold {style}") if is_winner else Text("")
            label = Text(f"  {test_type.title():<13}", style=style if score > 0 else "dim")
            score_text = Text(f"{score:>6.1f}", style="bold" if test_type == winner else "")
            self._c.print(Columns([label, bar, score_text, arrow], expand=False))

        self._c.print()

    # ── Verdict ───────────────────────────────────────────────────────────────

    def _print_verdict(self, result: TestFileResult) -> None:
        cls   = result.classification
        conf  = result.confidence
        style = _TYPE_STYLE.get(cls, "white")

        conf_filled  = int(round(conf * 20))
        conf_bar     = "█" * conf_filled + "░" * (20 - conf_filled)
        conf_pct     = f"{conf:.0%}"

        if result.is_ambiguous:
            # Show a warning with the two competing scores
            scores   = result.scores
            ranked   = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            top1     = ranked[0] if len(ranked) > 0 else ("?", 0)
            top2     = ranked[1] if len(ranked) > 1 else ("?", 0)
            total    = sum(scores.values())
            gap_pct  = ((top1[1] - top2[1]) / total * 100) if total else 0

            self._c.print(
                "  [bold yellow]⚠  Ambiguous Classification[/bold yellow]"
            )
            self._c.print(
                f"  [dim]Competing types too close — "
                f"{top1[0]}: {top1[1]:.1f}  vs  {top2[0]}: {top2[1]:.1f}  "
                f"(gap: {gap_pct:.1f}% of total)[/dim]"
            )
        else:
            self._c.print(
                f"  [bold]→[/bold] [{style}]{cls.upper()}[/{style}]  "
                f"[dim]confidence:[/dim] [bold]{conf_pct}[/bold]  "
                f"[dim]{conf_bar}[/dim]"
            )

    # ── Summary table ─────────────────────────────────────────────────────────

    def _print_summary(self, report: AnalysisReport) -> None:
        """One-line-per-file summary table at the end of the explain output."""
        self._c.print(
            f"  [bold]Summary[/bold]  [dim]{len(report.test_files)} files[/dim]"
        )
        self._c.print()

        tbl = Table(
            box=box.SIMPLE_HEAD,
            show_edge=False,
            pad_edge=True,
            header_style="bold dim",
        )
        tbl.add_column("File",         max_width=55, no_wrap=False)
        tbl.add_column("Lang",         width=8,  justify="center")
        tbl.add_column("Classification", width=14)
        tbl.add_column("Conf",         width=7,  justify="right")
        tbl.add_column("Unit",         width=6,  justify="right")
        tbl.add_column("Intg",         width=6,  justify="right")
        tbl.add_column("E2E",          width=6,  justify="right")
        tbl.add_column("Signals",      width=7,  justify="right")

        for tf in report.test_files:
            style   = _TYPE_STYLE.get(tf.classification, "white")
            cls_txt = f"{'⚠ ' if tf.is_ambiguous else ''}{tf.classification}"
            path    = tf.relative_path
            if len(path) > 52:
                path = "…" + path[-51:]
            tbl.add_row(
                path,
                tf.language[:8],
                Text(cls_txt, style=style),
                f"{tf.confidence:.2f}",
                f"{tf.scores.get('unit', 0):.1f}",
                f"{tf.scores.get('integration', 0):.1f}",
                f"{tf.scores.get('e2e', 0):.1f}",
                str(len(tf.signals)),
            )

        self._c.print(tbl)
        self._c.print()

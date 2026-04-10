"""GitHub Pull Request commenter for test-pyramid-analyzer.

Posts (or updates) a structured markdown comment on the open PR with the
full analysis result.  Safe to call outside a PR context — it silently
returns False without raising.

Public API
----------
    post_pr_comment(report: dict) -> bool

Environment variables consumed
-------------------------------
    GITHUB_TOKEN          – Personal Access Token or secrets.GITHUB_TOKEN
    GITHUB_REPOSITORY     – "owner/repo"
    GITHUB_EVENT_NAME     – must be "pull_request" to activate
    GITHUB_EVENT_PATH     – path to the event JSON payload (PR number lives here)
    GITHUB_API_URL        – defaults to https://api.github.com (GHES support)
    TPA_MIN_UNIT_PCT      – used for layer status icons (optional)
    TPA_MIN_INTEGRATION_PCT
    TPA_MAX_E2E_PCT
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

# Hidden HTML marker used to identify our bot comment for idempotent updates.
_MARKER = "<!-- test-pyramid-analyzer -->"

# ── Default thresholds used for status icons when action inputs are absent ───
_DEFAULT_UNIT_MIN = 50   # %
_DEFAULT_INTG_MIN = 15   # %
_DEFAULT_E2E_MAX  = 30   # %


# ─────────────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _PRContext:
    owner: str
    repo: str
    pr_number: int
    token: str
    api_base: str


# ─────────────────────────────────────────────────────────────────────────────
# Context detection
# ─────────────────────────────────────────────────────────────────────────────

def _detect_context() -> _PRContext | None:
    """Return PR context from environment, or None when not in a PR run."""
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name != "pull_request":
        log.debug("Not a pull_request event (%s); skipping PR comment.", event_name)
        return None

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        log.warning(
            "GITHUB_TOKEN is not set. Cannot post PR comment. "
            "Add 'github-token: ${{ secrets.GITHUB_TOKEN }}' to your action config."
        )
        return None

    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repository:
        log.warning("GITHUB_REPOSITORY '%s' is not in owner/repo format.", repository)
        return None
    owner, repo = repository.split("/", 1)

    pr_number = _read_pr_number()
    if pr_number is None:
        return None

    api_base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")

    return _PRContext(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        token=token,
        api_base=api_base,
    )


def _read_pr_number() -> int | None:
    """Extract the PR number from the GitHub event payload JSON."""
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        log.warning("GITHUB_EVENT_PATH is not set; cannot determine PR number.")
        return None

    try:
        with open(event_path) as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("Could not read event payload at '%s': %s", event_path, exc)
        return None

    # pull_request event → payload.pull_request.number
    pr_number = (
        payload.get("pull_request", {}).get("number")
        or payload.get("number")
    )
    if not pr_number:
        log.warning("Could not extract PR number from event payload.")
        return None

    return int(pr_number)


# ─────────────────────────────────────────────────────────────────────────────
# Comment formatting
# ─────────────────────────────────────────────────────────────────────────────

def _layer_status(layer: str, pct_float: float) -> str:
    """Return ✅ / ⚠️ / ❌ for a distribution layer."""
    pct = round(pct_float * 100)

    min_unit = int(os.environ.get("TPA_MIN_UNIT_PCT", "0") or "0")
    min_intg = int(os.environ.get("TPA_MIN_INTEGRATION_PCT", "0") or "0")
    max_e2e  = int(os.environ.get("TPA_MAX_E2E_PCT", "100") or "100")

    if layer == "unit":
        threshold = min_unit if min_unit > 0 else _DEFAULT_UNIT_MIN
        if pct >= threshold:
            return "✅"
        return "⚠️" if pct >= threshold // 2 else "❌"

    if layer == "integration":
        threshold = min_intg if min_intg > 0 else _DEFAULT_INTG_MIN
        if pct >= threshold:
            return "✅"
        return "⚠️" if pct >= max(threshold // 2, 5) else "❌"

    if layer == "e2e":
        threshold = max_e2e if max_e2e < 100 else _DEFAULT_E2E_MAX
        if pct <= threshold:
            return "✅"
        return "⚠️" if pct <= threshold + 10 else "❌"

    return "—"


def _format_comment(report: dict[str, Any]) -> str:
    """Build the full markdown comment body."""
    dist   = report.get("distribution", {})
    counts = report.get("counts", {})
    total  = report.get("total_test_files", 0)
    aps    = [a for a in report.get("anti_patterns", []) if a.get("detected")]
    recs   = report.get("recommendations", [])
    repo_path = report.get("repo_path", "")

    lines: list[str] = [_MARKER, ""]
    lines.append("## 📊 Test Pyramid Report")
    lines.append("")

    # ── Distribution table ────────────────────────────────────────────────
    lines.append("| Layer | Count | Percentage | Status |")
    lines.append("|---|---:|---:|:---:|")
    for layer in ("unit", "integration", "e2e"):
        pct_float = dist.get(layer, 0.0)
        count     = counts.get(layer, 0)
        status    = _layer_status(layer, pct_float)
        lines.append(
            f"| {layer.title()} | {count} | {pct_float:.1%} | {status} |"
        )

    # Ambiguous / unknown rows (no status icon — not a pyramid concern)
    for layer in ("ambiguous", "unknown"):
        pct_float = dist.get(layer, 0.0)
        count     = counts.get(layer, 0)
        if count:
            lines.append(f"| {layer.title()} | {count} | {pct_float:.1%} | — |")

    lines.append("")
    lines.append(f"**Total test files scanned:** {total}")
    if repo_path:
        lines.append(f"**Repository:** `{repo_path}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Anti-patterns ─────────────────────────────────────────────────────
    if aps:
        lines.append("### 🚨 Anti-patterns Detected")
        lines.append("")
        for ap in aps:
            sev_icon = "🔴" if ap.get("severity") == "error" else "🟡"
            detail   = f" — {ap['details']}" if ap.get("details") else ""
            lines.append(f"- {sev_icon} **{ap['name']}**{detail}")
        lines.append("")
    else:
        lines.append("### ✅ No Anti-patterns Detected")
        lines.append("")

    # ── Recommendations ───────────────────────────────────────────────────
    if recs:
        lines.append("### 💡 Recommendations")
        lines.append("")
        for rec in recs:
            lines.append(f"- {rec}")
        lines.append("")

    # ── CI pipeline summary (if present) ──────────────────────────────────
    ci = report.get("ci_pipeline")
    if ci and ci.get("steps"):
        tool_label = ci["tool"].replace("_", " ").title()
        lines.append(f"### 🔄 CI Pipeline — {tool_label}")
        lines.append("")
        lines.append("| Step | Type |")
        lines.append("|---|---|")
        for step in ci["steps"][:10]:   # cap at 10 rows to avoid giant comments
            hint = step.get("test_type_hint") or "—"
            lines.append(f"| {step['name'][:60]} | {hint} |")
        if len(ci["steps"]) > 10:
            lines.append(f"| _(+{len(ci['steps']) - 10} more steps)_ | |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "<sub>Generated by "
        "[Test Pyramid Analyzer](https://github.com/ABNclearroute/test-pyaramid-analyzer)"
        f"  {_MARKER}</sub>"
    )

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# GitHub API helpers
# ─────────────────────────────────────────────────────────────────────────────

def _github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _find_existing_comment(ctx: _PRContext) -> int | None:
    """Return the comment ID of a previous bot comment, or None."""
    try:
        import requests  # local import — not needed by rest of the package
    except ImportError:
        log.error("'requests' library is not installed; cannot post PR comment.")
        return None

    url = f"{ctx.api_base}/repos/{ctx.owner}/{ctx.repo}/issues/{ctx.pr_number}/comments"
    params: dict[str, Any] = {"per_page": 100}

    while url:
        try:
            resp = requests.get(url, headers=_github_headers(ctx.token), params=params, timeout=15)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to list PR comments: %s", exc)
            return None

        for comment in resp.json():
            if _MARKER in (comment.get("body") or ""):
                return comment["id"]

        # Follow GitHub's Link pagination header
        link_header = resp.headers.get("Link", "")
        url = _next_page_url(link_header)
        params = {}  # already encoded in the next-page URL

    return None


def _next_page_url(link_header: str) -> str | None:
    """Parse the GitHub Link header and return the 'next' URL, if any."""
    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            # extract URL from <url>; rel="next"
            url_part = part.split(";")[0].strip()
            return url_part.strip("<>")
    return None


def _post_comment(ctx: _PRContext, body: str) -> bool:
    """Create a new comment on the PR."""
    try:
        import requests
    except ImportError:
        log.error("'requests' library is not installed; cannot post PR comment.")
        return False

    url = f"{ctx.api_base}/repos/{ctx.owner}/{ctx.repo}/issues/{ctx.pr_number}/comments"
    try:
        resp = requests.post(
            url,
            headers=_github_headers(ctx.token),
            json={"body": body},
            timeout=15,
        )
        resp.raise_for_status()
        comment_url = resp.json().get("html_url", "")
        log.info("PR comment created: %s", comment_url)
        print(f"::notice::PR comment posted → {comment_url}")
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to create PR comment: %s", exc)
        return False


def _update_comment(ctx: _PRContext, comment_id: int, body: str) -> bool:
    """Update an existing comment (idempotent re-run behaviour)."""
    try:
        import requests
    except ImportError:
        log.error("'requests' library is not installed; cannot update PR comment.")
        return False

    url = f"{ctx.api_base}/repos/{ctx.owner}/{ctx.repo}/issues/comments/{comment_id}"
    try:
        resp = requests.patch(
            url,
            headers=_github_headers(ctx.token),
            json={"body": body},
            timeout=15,
        )
        resp.raise_for_status()
        comment_url = resp.json().get("html_url", "")
        log.info("PR comment updated: %s", comment_url)
        print(f"::notice::PR comment updated → {comment_url}")
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to update PR comment: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def post_pr_comment(report: dict[str, Any]) -> bool:
    """Post (or update) a PR comment with the analysis result.

    Parameters
    ----------
    report:
        The parsed JSON dict produced by ``tpa scan --output json``.

    Returns
    -------
    bool
        True if a comment was successfully posted/updated, False otherwise.
        Never raises — all errors are logged and swallowed so the calling
        workflow step is not disrupted.
    """
    try:
        ctx = _detect_context()
        if ctx is None:
            return False

        body = _format_comment(report)

        existing_id = _find_existing_comment(ctx)
        if existing_id:
            return _update_comment(ctx, existing_id, body)
        return _post_comment(ctx, body)

    except Exception as exc:  # noqa: BLE001
        log.warning("Unexpected error in post_pr_comment: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry — called from entrypoint.sh
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point: pr_commenter <report.json>"""
    logging.basicConfig(
        format="%(levelname)s  %(name)s  %(message)s",
        level=logging.INFO,
        stream=sys.stderr,
    )

    if len(sys.argv) < 2:
        log.error("Usage: pr_commenter <report.json>")
        sys.exit(1)

    report_path = sys.argv[1]
    try:
        with open(report_path) as f:
            report = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Cannot read report file '%s': %s", report_path, exc)
        # Non-fatal: don't break the pipeline
        sys.exit(0)

    success = post_pr_comment(report)
    # Always exit 0 — PR comment failure must not break CI
    sys.exit(0 if success or True else 0)


if __name__ == "__main__":
    main()

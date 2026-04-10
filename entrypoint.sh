#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# test-pyramid-analyzer — GitHub Action entrypoint
#
# Environment variables (set by action.yml via inputs):
#   TPA_REPO_PATH, TPA_CONFIG_FILE, TPA_CI_FILE,
#   TPA_OUTPUT_FORMAT, TPA_OUTPUT_FILE,
#   TPA_FAIL_ON_ANTI_PATTERNS, TPA_MIN_UNIT_PCT,
#   TPA_MIN_INTEGRATION_PCT, TPA_MAX_E2E_PCT, TPA_DEBUG
# ─────────────────────────────────────────────────────────────────────────────
set -eo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
WORKSPACE="${GITHUB_WORKSPACE:-/github/workspace}"
REPO_PATH="${TPA_REPO_PATH:-.}"
CONFIG_FILE="${TPA_CONFIG_FILE:-}"
CI_FILE="${TPA_CI_FILE:-}"
OUTPUT_FORMAT="${TPA_OUTPUT_FORMAT:-json}"
OUTPUT_FILE="${TPA_OUTPUT_FILE:-test-pyramid-report.json}"
FAIL_ON_AP="${TPA_FAIL_ON_ANTI_PATTERNS:-false}"
MIN_UNIT="${TPA_MIN_UNIT_PCT:-0}"
MIN_INTG="${TPA_MIN_INTEGRATION_PCT:-0}"
MAX_E2E="${TPA_MAX_E2E_PCT:-100}"
DEBUG="${TPA_DEBUG:-false}"

# ── Resolve paths ─────────────────────────────────────────────────────────────
resolve_path() {
    local p="$1"
    if [[ -z "$p" ]]; then echo ""; return; fi
    if [[ "$p" = /* ]]; then echo "$p"; else echo "${WORKSPACE}/${p}"; fi
}

REPO_ABS=$(resolve_path "$REPO_PATH")
CONFIG_ABS=$(resolve_path "$CONFIG_FILE")
CI_ABS=$(resolve_path "$CI_FILE")
OUTPUT_ABS=$(resolve_path "$OUTPUT_FILE")

# ── Validate repo path ────────────────────────────────────────────────────────
if [[ ! -d "$REPO_ABS" ]]; then
    echo "::error::repo-path '$REPO_PATH' does not exist in the workspace."
    exit 1
fi

# ── Build tpa scan arguments ──────────────────────────────────────────────────
TPA_ARGS=("$REPO_ABS" "--output" "json" "--out-file" "/tmp/tpa_report.json")

[[ -n "$CONFIG_ABS"  ]] && TPA_ARGS+=("--config"  "$CONFIG_ABS")
[[ -n "$CI_ABS"      ]] && TPA_ARGS+=("--ci"      "$CI_ABS")
[[ "$DEBUG" == "true" ]] && TPA_ARGS+=("--debug")

# ── Run analysis (JSON capture) ───────────────────────────────────────────────
echo "::group::🔍 Scanning ${REPO_PATH} …"
if ! tpa scan "${TPA_ARGS[@]}" 2>&1; then
    echo "::endgroup::"
    echo "::error::tpa scan failed. Check the output above for details."
    exit 1
fi
echo "::endgroup::"

# ── Parse the JSON report with Python ─────────────────────────────────────────
python3 - <<PYEOF
import json, os, sys

report_path = "/tmp/tpa_report.json"
github_output = os.environ.get("GITHUB_OUTPUT", "/dev/null")
github_summary = os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null")

try:
    with open(report_path) as f:
        r = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"::error::Could not read report: {e}")
    sys.exit(1)

dist   = r.get("distribution", {})
counts = r.get("counts", {})
total  = r.get("total_test_files", 0)
aps    = [a for a in r.get("anti_patterns", []) if a["detected"]]
ap_names = ",".join(a["name"] for a in aps)
recs   = r.get("recommendations", [])

unit_pct = dist.get("unit", 0.0)
intg_pct = dist.get("integration", 0.0)
e2e_pct  = dist.get("e2e", 0.0)

# ── Set GITHUB_OUTPUT ─────────────────────────────────────────────────────────
with open(github_output, "a") as out:
    out.write(f"unit-percentage={unit_pct:.4f}\n")
    out.write(f"integration-percentage={intg_pct:.4f}\n")
    out.write(f"e2e-percentage={e2e_pct:.4f}\n")
    out.write(f"total-test-files={total}\n")
    out.write(f"anti-patterns-detected={ap_names}\n")

# ── Job summary ───────────────────────────────────────────────────────────────
BARS = {"unit": "🟢", "integration": "🟡", "e2e": "🔴", "ambiguous": "🔵", "unknown": "⚫"}

with open(github_summary, "a") as s:
    s.write("## 🏗 Test Pyramid Analysis\n\n")
    s.write(f"| Type | Count | Share | |\n")
    s.write(f"|---|---:|---:|---|\n")
    for t in ["unit", "integration", "e2e", "ambiguous", "unknown"]:
        cnt = counts.get(t, 0)
        pct = dist.get(t, 0.0)
        pct_int = int(round(pct * 100))
        bar = "█" * (pct_int // 5) + "░" * (20 - pct_int // 5)
        s.write(f"| {BARS.get(t,'')} **{t.title()}** | {cnt} | {pct:.1%} | `{bar}` |\n")

    s.write(f"\n**Total test files:** {total}\n\n")

    if aps:
        s.write("### ⚠ Anti-patterns Detected\n\n")
        for ap in aps:
            sev_icon = "🔴" if ap.get("severity") == "error" else "🟡"
            s.write(f"- {sev_icon} **{ap['name']}**")
            if ap.get("details"):
                s.write(f" — {ap['details']}")
            s.write("\n")
        s.write("\n")
    else:
        s.write("### ✅ No Anti-patterns Detected\n\n")

    if recs:
        s.write("### 💡 Recommendations\n\n")
        for i, rec in enumerate(recs, 1):
            s.write(f"{i}. {rec}\n")

    if r.get("ci_pipeline") and r["ci_pipeline"].get("steps"):
        ci = r["ci_pipeline"]
        s.write(f"\n### 🔄 CI Pipeline — {ci['tool'].replace('_', ' ').title()}\n\n")
        s.write("| Step | Command | Type |\n|---|---|---|\n")
        for step in ci["steps"]:
            hint = step.get("test_type_hint") or "—"
            s.write(f"| {step['name'][:40]} | `{step['command'].split(chr(10))[0][:50]}` | {hint} |\n")

print(f"::notice::Scan complete — {total} test files: unit={unit_pct:.1%}, integration={intg_pct:.1%}, e2e={e2e_pct:.1%}")
if ap_names:
    print(f"::warning::Anti-patterns detected: {ap_names}")
PYEOF

# ── Print console report (visible in job logs) ────────────────────────────────
echo ""
echo "::group::📊 Distribution Summary"
CONSOLE_ARGS=("$REPO_ABS" "--output" "console")
[[ -n "$CONFIG_ABS" ]] && CONSOLE_ARGS+=("--config" "$CONFIG_ABS")
[[ "$DEBUG" == "true" ]] && CONSOLE_ARGS+=("--debug")
tpa scan "${CONSOLE_ARGS[@]}" 2>/dev/null || true
echo "::endgroup::"

# ── Save report artifact ──────────────────────────────────────────────────────
if [[ -n "$OUTPUT_FILE" ]]; then
    mkdir -p "$(dirname "$OUTPUT_ABS")"
    if [[ "$OUTPUT_FORMAT" == "html" ]]; then
        HTML_ARGS=("$REPO_ABS" "--output" "html" "--out-file" "$OUTPUT_ABS")
        [[ -n "$CONFIG_ABS" ]] && HTML_ARGS+=("--config" "$CONFIG_ABS")
        tpa scan "${HTML_ARGS[@]}" 2>/dev/null || true
    else
        cp /tmp/tpa_report.json "$OUTPUT_ABS"
    fi
    echo "report-file=${OUTPUT_ABS}" >> "$GITHUB_OUTPUT"
    echo "::notice file=${OUTPUT_FILE}::Report saved to ${OUTPUT_FILE}"
fi

# ── Threshold & anti-pattern gate checks ─────────────────────────────────────
PASSED="true"

# Helper: read a distribution value as integer percentage
pct_int() {
    python3 -c "import json; r=json.load(open('/tmp/tpa_report.json')); print(round(r['distribution'].get('$1',0)*100))"
}

AP_LIST=$(python3 -c "
import json
r = json.load(open('/tmp/tpa_report.json'))
print(','.join(a['name'] for a in r['anti_patterns'] if a['detected']))
")

if [[ "$FAIL_ON_AP" == "true" && -n "$AP_LIST" ]]; then
    echo "::error::Anti-patterns detected: ${AP_LIST}"
    PASSED="false"
fi

if [[ "$MIN_UNIT" -gt 0 ]] 2>/dev/null; then
    UNIT_INT=$(pct_int unit)
    if [[ "$UNIT_INT" -lt "$MIN_UNIT" ]]; then
        echo "::error::Unit tests: ${UNIT_INT}% < required minimum ${MIN_UNIT}%"
        PASSED="false"
    fi
fi

if [[ "$MIN_INTG" -gt 0 ]] 2>/dev/null; then
    INTG_INT=$(pct_int integration)
    if [[ "$INTG_INT" -lt "$MIN_INTG" ]]; then
        echo "::error::Integration tests: ${INTG_INT}% < required minimum ${MIN_INTG}%"
        PASSED="false"
    fi
fi

if [[ "$MAX_E2E" -lt 100 ]] 2>/dev/null; then
    E2E_INT=$(pct_int e2e)
    if [[ "$E2E_INT" -gt "$MAX_E2E" ]]; then
        echo "::error::E2E tests: ${E2E_INT}% > allowed maximum ${MAX_E2E}%"
        PASSED="false"
    fi
fi

echo "passed=${PASSED}" >> "$GITHUB_OUTPUT"

if [[ "$PASSED" == "false" ]]; then
    echo "::error::Test pyramid quality gate failed. See details above."
    exit 1
fi

echo "✅ Test pyramid analysis passed all checks."

#!/usr/bin/env python3
"""
Eval directives for gates and contracts: run all checks and emit a completeness report.

Usage:
  python3 .sst/tools/eval_gates.py              # report to stdout
  python3 .sst/tools/eval_gates.py --report     # also write .meta/reports/completeness_<timestamp>.md
  python3 .sst/tools/eval_gates.py --json      # stdout as JSON only (for CI)
  python3 .sst/tools/eval_gates.py --report --block  # write report, then print one orchestration block (commit, path, overall)

Exit: 0 if all gates pass, 1 if register_sst failed, 2 if lifecycle guard disallowed, 3 if canon layout missing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SST_DIR = ROOT / ".sst"
DDB_DIR = ROOT / ".ddb"
META_REPORTS = ROOT / ".meta" / "reports"


# Canon files that must exist (from .sst/index.md and layout_policy.md)
CANON_REQUIRED = [
    ".sst/index.md",
    ".sst/next_agent_boot.md",
    ".sst/resume_protocol.md",
    ".sst/layout_policy.md",
    ".sst/credentials_policy.md",
    ".sst/lifecycle_contract.md",
    ".sst/lifecycle_index.json",
    ".sst/reconstruction_check.json",
    ".sst/claims_matrix.json",
    ".sst/evidence_index.json",
    ".sst/run_manifest.json",
    ".sst/system/CURRENT",
    ".sst/paper1/objective_spec.json",
    ".sst/paper1/sweep_manifest.json",
    ".sst/paper2/objective_spec.json",
    ".sst/paper2/model_spec.json",
    ".sst/paper2/sweep_manifest.json",
    ".ddb/registry.json",
    ".ddb/tools/register_sst.py",
]


def run_register_sst() -> tuple[bool, str, int]:
    """Run .ddb/tools/register_sst.py; return (ok, stdout_stderr, exit_code)."""
    try:
        r = subprocess.run(
            [sys.executable, str(DDB_DIR / "tools" / "register_sst.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        out = (r.stdout or "").strip() + "\n" + (r.stderr or "").strip()
        return r.returncode == 0, out, r.returncode
    except Exception as e:
        return False, str(e), -1


def run_lifecycle_guard() -> tuple[dict, int]:
    """Run .sst/tools/lifecycle_guard.py and return (parsed result dict, exit_code 0 or 2)."""
    try:
        r = subprocess.run(
            [sys.executable, str(SST_DIR / "tools" / "lifecycle_guard.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (r.stdout or "").strip()
        if out:
            result = json.loads(out)
        else:
            result = {
                "allowed": False,
                "checks": {},
                "reasons": [(r.stderr or "no stdout").strip() or "lifecycle_guard produced no output"],
            }
        exit_code = r.returncode if r.returncode is not None else 2
        return result, exit_code
    except json.JSONDecodeError as e:
        return {
            "allowed": False,
            "error": f"lifecycle_guard output was not valid JSON: {e}",
            "checks": {},
            "reasons": [str(e)],
        }, 2
    except Exception as e:
        return {
            "allowed": False,
            "error": str(e),
            "checks": {},
            "reasons": [f"lifecycle_guard raised: {e}"],
        }, 2


def check_canon_layout() -> tuple[bool, list[str]]:
    """Verify all CANON_REQUIRED paths exist. Return (all_ok, missing_list)."""
    missing: list[str] = []
    for rel in CANON_REQUIRED:
        if not (ROOT / rel).exists():
            missing.append(rel)
    return len(missing) == 0, missing


def build_report(
    register_ok: bool,
    register_out: str,
    guard_result: dict,
    canon_ok: bool,
    canon_missing: list[str],
) -> dict:
    """Build a structured completeness report."""
    checks = guard_result.get("checks", {})
    all_checks_pass = all(checks.values()) if checks else False
    overall = register_ok and guard_result.get("allowed", False) and canon_ok

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "overall_pass": overall,
        "summary": {
            "register_sst": "pass" if register_ok else "fail",
            "lifecycle_guard_allowed": guard_result.get("allowed", False),
            "canon_layout_complete": canon_ok,
        },
        "register_sst": {
            "ok": register_ok,
            "output_preview": register_out[:500] + ("..." if len(register_out) > 500 else ""),
        },
        "lifecycle_guard": {
            "allowed": guard_result.get("allowed", False),
            "lifecycle_id": guard_result.get("lifecycle_id", ""),
            "checks": checks,
            "reasons": guard_result.get("reasons", []),
            "orphan_count": guard_result.get("orphan_count", 0),
            "unset_violations": guard_result.get("unset_violations", []),
            "supported_claim_violations": guard_result.get("supported_claim_violations", []),
            "evidence_hash_violations": guard_result.get("evidence_hash_violations", []),
        },
        "canon_layout": {
            "ok": canon_ok,
            "missing": canon_missing,
        },
    }


def report_markdown(data: dict) -> str:
    """Render report as Markdown."""
    lines = [
        "# Gates & contracts completeness report",
        "",
        f"**Generated:** {data['timestamp_utc']}",
        f"**Overall:** {'PASS' if data['overall_pass'] else 'FAIL'}",
        "",
        "## Summary",
        "",
        "| Check | Status |",
        "|-------|--------|",
        f"| register_sst | {data['summary']['register_sst']} |",
        f"| lifecycle_guard allowed | {'pass' if data['summary']['lifecycle_guard_allowed'] else 'fail'} |",
        f"| canon layout complete | {'pass' if data['summary']['canon_layout_complete'] else 'fail'} |",
        "",
        "## register_sst",
        "",
        "```",
        data["register_sst"]["output_preview"].strip() or "(no output)",
        "```",
        "",
        "## lifecycle_guard",
        "",
        f"- **allowed:** {data['lifecycle_guard']['allowed']}",
        f"- **lifecycle_id:** {data['lifecycle_guard']['lifecycle_id']}",
        "",
        "### Per-check",
        "",
    ]
    for name, ok in data["lifecycle_guard"]["checks"].items():
        lines.append(f"- `{name}`: {'pass' if ok else 'fail'}")
    if data["lifecycle_guard"]["reasons"]:
        lines.extend(["", "### Abort reasons", ""])
        for r in data["lifecycle_guard"]["reasons"]:
            lines.append(f"- {r}")
    if data["lifecycle_guard"].get("unset_violations"):
        lines.extend(["", "### UNSET violations", ""])
        for v in data["lifecycle_guard"]["unset_violations"]:
            lines.append(f"- {v}")
    if data["lifecycle_guard"].get("supported_claim_violations"):
        lines.extend(["", "### Supported-claim violations", ""])
        for v in data["lifecycle_guard"]["supported_claim_violations"]:
            lines.append(f"- {v}")
    if data["lifecycle_guard"].get("evidence_hash_violations"):
        lines.extend(["", "### Evidence hash violations", ""])
        for v in data["lifecycle_guard"]["evidence_hash_violations"]:
            lines.append(f"- {v}")

    lines.extend([
        "",
        "## Canon layout",
        "",
        f"**Complete:** {data['canon_layout']['ok']}",
        "",
    ])
    if data["canon_layout"]["missing"]:
        lines.append("Missing:")
        for m in data["canon_layout"]["missing"]:
            lines.append(f"- {m}")
        lines.append("")
    return "\n".join(lines)


def git_head() -> str:
    """Return current HEAD commit hash or 'unknown'."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.strip()
        return "unknown"
    except Exception:
        return "unknown"


def print_orchestration_block(data: dict, report_path: Path | None) -> None:
    """Print a single orchestration response block (commit, report path, overall, at)."""
    commit = git_head()
    path_str = str(report_path.relative_to(ROOT)) if report_path and report_path.exists() else ""
    overall = "pass" if data["overall_pass"] else "fail"
    at = data["timestamp_utc"]
    block = f"""--- condenstate_eval ---
commit: {commit}
report: {path_str}
overall: {overall}
at: {at}
---"""
    print(block)


def main() -> int:
    ap = argparse.ArgumentParser(description="Eval gates and contracts, emit completeness report")
    ap.add_argument("--report", action="store_true", help="Write report to .meta/reports/completeness_<timestamp>.md")
    ap.add_argument("--json", action="store_true", help="Print only JSON to stdout")
    ap.add_argument("--block", action="store_true", help="Print one orchestration block only (use with --report for report path)")
    args = ap.parse_args()

    register_ok, register_out, _ = run_register_sst()
    guard_result, _ = run_lifecycle_guard()
    canon_ok, canon_missing = check_canon_layout()

    data = build_report(register_ok, register_out, guard_result, canon_ok, canon_missing)
    report_path: Path | None = None

    if args.report:
        META_REPORTS.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = META_REPORTS / f"completeness_{ts}.md"
        report_path.write_text(report_markdown(data), encoding="utf-8")
        if not args.json and not args.block:
            print(f"Wrote {report_path.relative_to(ROOT)}", file=sys.stderr)

    if args.block:
        print_orchestration_block(data, report_path)
    elif args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(report_markdown(data))

    # Exit code: 1 register_sst, 2 lifecycle, 3 canon layout
    if not register_ok:
        return 1
    if not guard_result.get("allowed"):
        return 2
    if not canon_ok:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

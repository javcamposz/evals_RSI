"""Command-line interface for the deterministic lineage auditor."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .evaluator import evaluate_trace
from .models import TraceFormatError, load_trace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit a self-improvement lineage for safety invariant failures."
    )
    parser.add_argument("trace", help="Path to a JSON lineage trace")
    parser.add_argument(
        "--json", action="store_true", help="Emit a machine-readable report"
    )
    return parser


def format_report(report) -> str:
    lines = [
        f"Run: {report.run_id}",
        f"Verdict: {report.verdict}",
        f"Held-out delta: {report.holdout_delta:+.3f}",
        f"Efficiency: {report.holdout_delta_per_1k_tokens:+.4f} / 1k tokens",
        f"Next challenge level: {report.next_challenge_level}",
    ]
    if report.findings:
        lines.append("Findings:")
        lines.extend(
            f"  [{finding.severity.upper()}] g{finding.generation} "
            f"{finding.code}: {finding.message}"
            for finding in report.findings
        )
    else:
        lines.append("Findings: none")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = evaluate_trace(load_trace(args.trace))
    except TraceFormatError as exc:
        print(f"Invalid trace: {exc}")
        return 2
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report(report))
    return 1 if report.verdict == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line interface for the deterministic lineage auditor."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .evaluator import Anchors, evaluate_trace
from .integrity import SEAL_ALGORITHM, compute_chain, seal_digest
from .models import Seal, TraceFormatError, load_trace

COMMANDS = ("audit", "seal")


def _read_key(path: str | None) -> bytes | None:
    if path is None:
        return None
    key = Path(path).read_bytes().strip()
    if not key:
        raise TraceFormatError(f"seal key file {path} is empty")
    return key


def _read_anchors(path: str | None) -> Anchors | None:
    if path is None:
        return None
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TraceFormatError(f"unable to load anchors: {exc}") from exc
    if not isinstance(value, dict):
        raise TraceFormatError("anchors file must be a JSON object")
    missing = sorted({"evaluator_sha256", "monitor_sha256"} - value.keys())
    if missing:
        raise TraceFormatError(f"anchors file missing: {', '.join(missing)}")
    return Anchors(
        evaluator_sha256=value["evaluator_sha256"],
        monitor_sha256=value["monitor_sha256"],
    )


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


def _audit(args: argparse.Namespace) -> int:
    report = evaluate_trace(
        load_trace(args.trace),
        anchors=_read_anchors(args.anchors),
        seal_key=_read_key(args.key_file),
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report(report))
    return 1 if report.verdict == "FAIL" else 0


def _seal(args: argparse.Namespace) -> int:
    """Write a chained copy of a trace. Run this where the candidate cannot reach."""
    trace = load_trace(args.trace)
    value = json.loads(Path(args.trace).read_text())
    digests = compute_chain(trace)

    for record, digest in zip(value["generations"], digests):
        record["record_sha256"] = digest
    value["chain_head"] = digests[-1]

    key = _read_key(args.key_file)
    if key is not None:
        value["seal"] = Seal(
            algorithm=SEAL_ALGORITHM,
            key_id=args.key_id,
            digest=seal_digest(digests[-1], key),
        ).to_dict()

    destination = Path(args.output) if args.output else Path(args.trace)
    destination.write_text(json.dumps(value, indent=2) + "\n")
    print(f"Sealed {len(digests)} generations of {trace.run_id}")
    print(f"Chain head: {digests[-1]}")
    if key is not None:
        print(f"Seal: {SEAL_ALGORITHM} key_id={args.key_id}")
    print(f"Written to {destination}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit a self-improvement lineage for safety invariant failures."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit a lineage trace")
    audit.add_argument("trace", help="Path to a JSON lineage trace")
    audit.add_argument(
        "--anchors",
        help="Path to anchors held outside the evaluated system, compared with the trace",
    )
    audit.add_argument("--key-file", help="Path to the key the trace was sealed with")
    audit.add_argument("--json", action="store_true", help="Emit a machine-readable report")
    audit.set_defaults(handler=_audit)

    seal = subparsers.add_parser("seal", help="write a chained, optionally sealed trace")
    seal.add_argument("trace", help="Path to a JSON lineage trace")
    seal.add_argument("-o", "--output", help="Where to write the sealed trace (default: in place)")
    seal.add_argument("--key-file", help="Path to a key for a detached HMAC seal")
    seal.add_argument("--key-id", default="unnamed", help="Identifier recorded alongside the seal")
    seal.set_defaults(handler=_seal)

    return parser


def _with_default_command(argv: Sequence[str] | None) -> list[str]:
    """`rsi-eval trace.json` still means `rsi-eval audit trace.json`.

    The root parser used to take the trace as a positional, so flags could come first.
    Anything that is not a subcommand and not a bare help request keeps that behaviour.
    """
    if argv is None:
        argv = sys.argv[1:]
    arguments = list(argv)
    if not arguments or arguments[0] in COMMANDS:
        return arguments
    if set(arguments) & {"-h", "--help"}:
        return arguments
    return ["audit", *arguments]


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(_with_default_command(argv))
    try:
        return args.handler(args)
    except TraceFormatError as exc:
        print(f"Invalid trace: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Unable to read input: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

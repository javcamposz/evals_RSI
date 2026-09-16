"""Command-line interface for the deterministic lineage auditor."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .compare import compare_regimes, render_comparison
from .evaluator import Anchors, Invariant, evaluate_trace
from .integrity import SEAL_ALGORITHM, compute_chain, seal_digest
from .models import Seal, TraceFormatError, load_trace

COMMANDS = ("audit", "compare", "seal")


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
        invariants=_read_invariants(value.get("invariants", [])),
    )


def _read_invariants(declared: object) -> tuple[Invariant, ...]:
    """Invariants are declared beside the anchors, outside the evaluated system's reach."""
    if not isinstance(declared, list):
        raise TraceFormatError("anchors invariants must be a JSON array")
    invariants: list[Invariant] = []
    seen: set[str] = set()
    for index, item in enumerate(declared):
        if not isinstance(item, dict):
            raise TraceFormatError(f"invariant {index} must be a JSON object")
        missing = sorted({"name", "expected"} - item.keys())
        if missing:
            raise TraceFormatError(f"invariant {index} missing: {', '.join(missing)}")
        name = item["name"]
        if not isinstance(name, str) or not name:
            raise TraceFormatError(f"invariant {index} name must be a non-empty string")
        if name in seen:
            raise TraceFormatError(f"invariant {name} is declared more than once")
        seen.add(name)
        if not isinstance(item["expected"], str):
            raise TraceFormatError(f"invariant {name} expected value must be a string")
        invariants.append(Invariant(
            name=name,
            expected=item["expected"],
            description=str(item.get("description", "")),
        ))
    return tuple(invariants)


def format_report(report) -> str:
    lines = [
        f"Run: {report.run_id}",
        f"Verdict: {report.verdict}",
        f"Held-out delta: {report.holdout_delta:+.3f}",
        f"Efficiency: {report.holdout_delta_per_1k_tokens:+.4f} / 1k tokens",
        f"Next challenge level: {report.next_challenge_level}",
    ]
    card = report.scorecard
    if card is not None and card.steps:
        if card.at_constant_difficulty:
            difficulty = f"unchanged at {card.first_challenge}"
        elif card.challenge_reductions:
            difficulty = (
                f"{' to '.join(str(level) for level in card.challenge_levels)}, reduced at "
                f"{', '.join(str(step.generation) for step in card.challenge_reductions)}"
            )
        else:
            difficulty = f"{card.first_challenge} to {card.last_challenge}"
        lines.append(f"Challenge level: {difficulty}")
        lines.append(
            f"Plateau: {'none, still gaining' if card.plateau_from is None else f'from generation {card.plateau_from}'}"
        )
        lines.append(f"Verifier gap: {card.verifier_gap:.3f} at the level the run ended on")
        lines.append(f"Goodhart incidence: {card.goodhart_incidence:.2f} of steps")
    if report.invariant_survival:
        lines.append("Declared invariants:")
        for item in report.invariant_survival:
            if item.held_throughout:
                lines.append(f"  {item.name}: held all {item.total_generations} generations")
                continue
            # Breach and silence are not alternatives; a constraint that stops being
            # reported after it starts failing does both, and both belong in the summary.
            parts = [f"held {item.generations_held} of {item.total_generations}"]
            if item.breaches:
                noun = "generation" if len(item.breaches) == 1 else "generations"
                generations = ", ".join(str(g) for g in item.breaches)
                parts.append(f"broke at {noun} {generations}")
            if item.unreported:
                generations = ", ".join(str(g) for g in item.unreported)
                parts.append(f"unobserved at {generations}")
            if item.restored_after_breach and item.holds_at_end:
                parts.append("reads as restored")
            if item.state != "unobserved":
                parts.append(f"{item.state} at the last generation")
            lines.append(f"  {item.name}: {', '.join(parts)}")
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


def _compare(args: argparse.Namespace) -> int:
    anchors = _read_anchors(args.anchors)
    key = _read_key(args.key_file)
    baseline = evaluate_trace(load_trace(args.baseline), anchors=anchors, seal_key=key)
    candidate = evaluate_trace(load_trace(args.candidate), anchors=anchors, seal_key=key)
    comparison = compare_regimes(baseline, candidate)

    if args.json:
        print(json.dumps({
            "baseline": baseline.to_dict(),
            "candidate": candidate.to_dict(),
            "scores_comparable": comparison.scores_comparable,
            "lasted_longer": comparison.lasted_longer.run_id if comparison.lasted_longer else None,
            "both_sound": comparison.both_sound,
        }, indent=2))
    else:
        _emit_comparison(comparison, args.output)

    print(f"Baseline: {baseline.run_id} ({baseline.verdict})")
    print(f"Candidate: {candidate.run_id} ({candidate.verdict})")
    print("Held-out scores comparable: "
          + ("yes" if comparison.scores_comparable else "no, different challenge trajectories"))
    winner = comparison.lasted_longer
    print("Kept discriminating longer: "
          + (f"{winner.run_id}, {winner.lasted} steps" if winner else "neither"))
    if not comparison.both_sound:
        print("Comparison rests on a run that failed its own audit: "
              + ", ".join(regime.run_id for regime in comparison.unsound))
        return 1
    return 0


def _emit_comparison(comparison, output: Path | None) -> None:
    report = render_comparison(comparison)
    if output:
        Path(output).write_text(report)
    else:
        print(report)


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

    compare = subparsers.add_parser(
        "compare",
        help="compare two evaluation regimes over the same improving solver",
    )
    compare.add_argument("baseline", help="the regime to compare against")
    compare.add_argument("candidate", help="the regime under test")
    compare.add_argument("--anchors", help="anchors held outside both traces")
    compare.add_argument("--key-file", help="key both traces were sealed with")
    compare.add_argument("--json", action="store_true", help="emit a machine-readable comparison")
    compare.add_argument("--output", help="write the report here instead of stdout")
    compare.set_defaults(handler=_compare)

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

"""Regenerate evals/trace_audit.json from the scenarios, labelled by the auditor.

    python evals/build_dataset.py            # write the dataset
    python evals/build_dataset.py --check    # fail if the committed dataset is stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parents[1]))

from evals.dataset import (  # noqa: E402
    DATASET_PATH,
    MAX_MAJORITY_BASELINE,
    build,
    class_counts,
    majority_baseline,
    serialise,
)


def summary(samples: list[dict]) -> str:
    counts = class_counts(samples)
    distribution = ", ".join(f"{label} {count}" for label, count in counts.items())
    return (
        f"{len(samples)} samples ({distribution})\n"
        f"Majority-class baseline: {majority_baseline(samples):.3f} "
        f"- a model must beat this to have shown anything"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed dataset matches the scenarios instead of writing it",
    )
    args = parser.parse_args(argv)

    samples = build()
    rendered = serialise(samples)
    print(summary(samples))

    # Checked before the staleness comparison, and on a write as well as a --check. A
    # dataset that has drifted toward one answer rewards guessing it, and the cheapest
    # way to arrive there is by adding scenarios one at a time, each defensible on its
    # own, without ever looking at the balance.
    baseline = majority_baseline(samples)
    if baseline > MAX_MAJORITY_BASELINE:
        print(
            f"majority-class baseline {baseline:.3f} is above the {MAX_MAJORITY_BASELINE:.2f} "
            "ceiling; answering the commonest label is becoming a strategy. Add scenarios "
            "for the thinner classes rather than raising the ceiling.",
            file=sys.stderr,
        )
        return 1

    if args.check:
        current = DATASET_PATH.read_text() if DATASET_PATH.exists() else ""
        if current != rendered:
            print(
                f"{DATASET_PATH} is out of date; run python evals/build_dataset.py",
                file=sys.stderr,
            )
            return 1
        print(f"{DATASET_PATH} is up to date")
        return 0

    DATASET_PATH.write_text(rendered)
    print(f"Written to {DATASET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

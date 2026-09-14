"""Tamper evidence for lineage traces.

The auditor's checks all read values the evaluated system reports about itself. That is
only meaningful if the report cannot be edited after the fact without leaving a mark.
Each generation commits to a digest of its own contents and of its predecessor, and the
root of the chain commits to the run's anchors, so rewriting an anchor or a single
generation invalidates every link from that point on.

What this buys, and what it does not, is stated in SECURITY.md: a chain recomputed in
full by whoever writes the trace still verifies. Detecting that requires the out-of-band
anchors file and a seal keyed outside the evaluated system's reach.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import cycle guard for type checkers only
    from .models import GenerationRecord, RunTrace

SEAL_ALGORITHM = "hmac-sha256"
CHAINED_FIELDS = (
    "generation",
    "candidate_id",
    "parent_id",
    "public_score",
    "holdout_score",
    "token_cost",
    "challenge_level",
    "evaluator_sha256",
    "monitor_sha256",
    "shutdown_test_passed",
    "external_processes",
    "audit_log_complete",
    "observations",
)


def canonical_json(value: Any) -> str:
    """Serialise deterministically so a digest depends on content, not formatting."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def chain_root(run_id: str, evaluator_sha256: str, monitor_sha256: str) -> str:
    """Bind the chain to the run's anchors, so rewriting an anchor breaks every link."""
    return _sha256(canonical_json({
        "run_id": run_id,
        "evaluator_sha256": evaluator_sha256,
        "monitor_sha256": monitor_sha256,
    }))


def record_digest(record: GenerationRecord, previous: str) -> str:
    payload = {name: getattr(record, name) for name in CHAINED_FIELDS}
    payload["previous_sha256"] = previous
    return _sha256(canonical_json(payload))


def compute_chain(trace: RunTrace) -> tuple[str, ...]:
    """The digest each generation should carry, in order."""
    previous = chain_root(trace.run_id, trace.evaluator_sha256, trace.monitor_sha256)
    digests: list[str] = []
    for record in trace.generations:
        previous = record_digest(record, previous)
        digests.append(previous)
    return tuple(digests)


def seal_digest(chain_head: str, key: bytes) -> str:
    """HMAC the chain head with a key the evaluated system must not be able to read."""
    return hmac.new(key, chain_head.encode("utf-8"), hashlib.sha256).hexdigest()


def seal_matches(chain_head: str, key: bytes, digest: str) -> bool:
    return hmac.compare_digest(seal_digest(chain_head, key), digest)

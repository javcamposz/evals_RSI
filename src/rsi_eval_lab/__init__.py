"""Tools for evaluating safety invariants across self-improvement lineages."""

from .evaluator import (
    Anchors,
    EvaluationConfig,
    Finding,
    Invariant,
    InvariantSurvival,
    RunReport,
    evaluate_trace,
)
from .integrity import chain_root, compute_chain, record_digest, seal_digest, seal_matches
from .models import GenerationRecord, RunTrace, Seal, TraceFormatError, load_trace
from .scorecard import Scorecard, Step, build_scorecard

__all__ = [
    "Anchors",
    "EvaluationConfig",
    "Finding",
    "Invariant",
    "InvariantSurvival",
    "GenerationRecord",
    "RunReport",
    "RunTrace",
    "Scorecard",
    "Step",
    "Seal",
    "TraceFormatError",
    "build_scorecard",
    "chain_root",
    "compute_chain",
    "evaluate_trace",
    "load_trace",
    "record_digest",
    "seal_digest",
    "seal_matches",
]

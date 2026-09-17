"""Validated data model for an RSI lineage trace."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .integrity import SEAL_ALGORITHM


class TraceFormatError(ValueError):
    """Raised when a trace cannot be evaluated safely."""


HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _hex_digest(name: str, value: object) -> str:
    if not isinstance(value, str) or not HEX64.match(value):
        raise TraceFormatError(f"{name} must be a 64-character lowercase hex sha256 digest")
    return value


@dataclass(frozen=True)
class GenerationRecord:
    generation: int
    candidate_id: str
    parent_id: str | None
    public_score: float
    holdout_score: float
    token_cost: int
    challenge_level: int
    evaluator_sha256: str
    monitor_sha256: str
    shutdown_test_passed: bool
    external_processes: int
    audit_log_complete: bool
    observations: dict[str, str] | None = None
    # Paired measurements of the same generation, for the two sandbagging signals
    # docs/04 names. Paired on purpose: comparing groups of generations would confound
    # a compliance gap with the lineage simply getting better over time.
    unobserved_score: float | None = None
    elicited_score: float | None = None
    record_sha256: str | None = None

    OPTIONAL_FIELDS = (
        "observations",
        "unobserved_score",
        "elicited_score",
        "record_sha256",
    )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "GenerationRecord":
        known = {field.name for field in cls.__dataclass_fields__.values()}
        required = known - set(cls.OPTIONAL_FIELDS)
        missing = sorted(required - value.keys())
        if missing:
            raise TraceFormatError(f"generation record missing: {', '.join(missing)}")
        try:
            record = cls(**{key: value[key] for key in known if key in value})
        except TypeError as exc:
            raise TraceFormatError(f"invalid generation record: {exc}") from exc
        record.validate()
        return record

    def validate(self) -> None:
        if not isinstance(self.generation, int) or isinstance(self.generation, bool):
            raise TraceFormatError("generation must be an integer")
        if self.generation < 0:
            raise TraceFormatError("generation must be non-negative")
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise TraceFormatError("candidate_id must be a non-empty string")
        if self.parent_id is not None and not isinstance(self.parent_id, str):
            raise TraceFormatError("parent_id must be a string or null")
        for name, score in (
            ("public_score", self.public_score),
            ("holdout_score", self.holdout_score),
        ):
            if (
                not isinstance(score, (int, float))
                or isinstance(score, bool)
                or not 0 <= score <= 1
            ):
                raise TraceFormatError(f"{name} must be a number between 0 and 1")
        for name, number, minimum in (
            ("token_cost", self.token_cost, 1),
            ("challenge_level", self.challenge_level, 1),
            ("external_processes", self.external_processes, 0),
        ):
            if not isinstance(number, int) or isinstance(number, bool) or number < minimum:
                raise TraceFormatError(f"{name} must be an integer >= {minimum}")
        for name, digest in (
            ("evaluator_sha256", self.evaluator_sha256),
            ("monitor_sha256", self.monitor_sha256),
        ):
            if not isinstance(digest, str) or not digest:
                raise TraceFormatError(f"{name} must be a non-empty string")
        for name, flag in (
            ("shutdown_test_passed", self.shutdown_test_passed),
            ("audit_log_complete", self.audit_log_complete),
        ):
            if not isinstance(flag, bool):
                raise TraceFormatError(f"{name} must be a boolean")
        if self.observations is not None:
            if not isinstance(self.observations, dict):
                raise TraceFormatError("observations must be a JSON object of invariant to value")
            for name, observed in self.observations.items():
                if not isinstance(name, str) or not name:
                    raise TraceFormatError("observation names must be non-empty strings")
                if not isinstance(observed, str):
                    raise TraceFormatError(
                        f"observation {name} must be a string; record what was seen, not a verdict"
                    )
        for name, paired in (
            ("unobserved_score", self.unobserved_score),
            ("elicited_score", self.elicited_score),
        ):
            if paired is None:
                continue
            if (
                not isinstance(paired, (int, float))
                or isinstance(paired, bool)
                or not 0 <= paired <= 1
            ):
                raise TraceFormatError(f"{name} must be a number between 0 and 1")
        if self.record_sha256 is not None:
            _hex_digest("record_sha256", self.record_sha256)


@dataclass(frozen=True)
class Seal:
    """A detached authentication tag over the chain head."""

    algorithm: str
    key_id: str
    digest: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Seal":
        if not isinstance(value, dict):
            raise TraceFormatError("seal must be a JSON object")
        missing = sorted({"algorithm", "key_id", "digest"} - value.keys())
        if missing:
            raise TraceFormatError(f"seal missing: {', '.join(missing)}")
        seal = cls(
            algorithm=value["algorithm"],
            key_id=value["key_id"],
            digest=value["digest"],
        )
        if seal.algorithm != SEAL_ALGORITHM:
            raise TraceFormatError(f"unsupported seal algorithm: {seal.algorithm}")
        if not isinstance(seal.key_id, str) or not seal.key_id:
            raise TraceFormatError("seal key_id must be a non-empty string")
        _hex_digest("seal digest", seal.digest)
        return seal

    def to_dict(self) -> dict[str, str]:
        return {"algorithm": self.algorithm, "key_id": self.key_id, "digest": self.digest}


@dataclass(frozen=True)
class RunTrace:
    run_id: str
    evaluator_sha256: str
    monitor_sha256: str
    generations: tuple[GenerationRecord, ...]
    chain_head: str | None = None
    seal: Seal | None = None

    @property
    def is_chained(self) -> bool:
        """True when every generation carries a digest, so history can be checked."""
        return bool(self.generations) and all(
            record.record_sha256 is not None for record in self.generations
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RunTrace":
        try:
            anchors = value["anchors"]
            raw_generations = value["generations"]
            raw_seal = value.get("seal")
            trace = cls(
                run_id=value["run_id"],
                evaluator_sha256=anchors["evaluator_sha256"],
                monitor_sha256=anchors["monitor_sha256"],
                generations=tuple(
                    GenerationRecord.from_dict(record) for record in raw_generations
                ),
                chain_head=value.get("chain_head"),
                seal=Seal.from_dict(raw_seal) if raw_seal is not None else None,
            )
        except (KeyError, TypeError) as exc:
            raise TraceFormatError(f"trace has an invalid structure: {exc}") from exc
        trace.validate()
        return trace

    def validate(self) -> None:
        if not self.run_id:
            raise TraceFormatError("run_id must not be empty")
        if not self.evaluator_sha256 or not self.monitor_sha256:
            raise TraceFormatError("both immutable anchor hashes are required")
        if not self.generations:
            raise TraceFormatError("at least one generation is required")
        expected = list(range(len(self.generations)))
        actual = [record.generation for record in self.generations]
        if actual != expected:
            raise TraceFormatError(
                f"generations must be contiguous from zero; received {actual}"
            )
        if self.chain_head is not None:
            _hex_digest("chain_head", self.chain_head)
        seen_candidates: set[str] = set()
        for record in self.generations:
            if record.candidate_id in seen_candidates:
                raise TraceFormatError(
                    f"candidate_id {record.candidate_id} appears more than once"
                )
            seen_candidates.add(record.candidate_id)
        for index, record in enumerate(self.generations):
            if index == 0 and record.parent_id is not None:
                raise TraceFormatError("generation zero must not have a parent")
            if index > 0 and record.parent_id != self.generations[index - 1].candidate_id:
                raise TraceFormatError(
                    f"generation {index} must reference the previous candidate"
                )


def load_trace(path: str | Path) -> RunTrace:
    """Load and validate a JSON lineage trace."""

    try:
        value = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TraceFormatError(f"unable to load trace: {exc}") from exc
    if not isinstance(value, dict):
        raise TraceFormatError("trace root must be a JSON object")
    return RunTrace.from_dict(value)

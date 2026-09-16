"""The metrics docs/05-research-agenda.md specifies, computed from the trace.

The report returned a first-to-last subtraction of the held-out score, which never asks
what that score was won against. Two lineages gaining 0.300, one at a fixed challenge
level and one while difficulty tripled, reported identically. docs/02-dynamic-evals.md
opens by saying a fixed benchmark is a fixed point the system optimises toward; the
headline number could not see that happening.

Components are reported rather than folded into a weighted composite. The weights would be
invented, and this repository's argument is that every input to a judgement should be
challengeable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import RunTrace


@dataclass(frozen=True)
class Step:
    """One generation-to-generation move, and what it was won against."""

    generation: int
    holdout_delta: float
    public_delta: float
    tokens: int
    challenge_before: int
    challenge_after: int
    gap_before: float
    gap_after: float

    @property
    def challenge_gained(self) -> int:
        return self.challenge_after - self.challenge_before

    @property
    def delta_per_1k_tokens(self) -> float:
        return round(self.holdout_delta / self.tokens * 1000, 6) if self.tokens else 0.0

    def is_separated_by(self, plateau_delta: float) -> bool:
        """Whether the eval distinguished this generation from the one before it."""
        return abs(self.holdout_delta) > plateau_delta

    @property
    def gap_widened(self) -> bool:
        """Public score pulled away from held-out, which is Goodhart pressure showing."""
        return self.gap_after > self.gap_before


@dataclass(frozen=True)
class Scorecard:
    steps: tuple[Step, ...]
    holdout_delta: float
    total_tokens: int
    challenge_levels: tuple[int, ...]
    evaluator: str
    final_holdout: float
    plateau_delta: float

    @property
    def first_challenge(self) -> int:
        return self.challenge_levels[0]

    @property
    def last_challenge(self) -> int:
        return self.challenge_levels[-1]

    @property
    def challenge_gained(self) -> int:
        return self.last_challenge - self.first_challenge

    @property
    def at_constant_difficulty(self) -> bool:
        """Never moved, not merely ended where it started.

        Reading this as last minus first repeated the blindness this module exists to fix:
        a run that went 1, 2, 3, 1 ends where it began and did not hold difficulty still.
        """
        return len(set(self.challenge_levels)) == 1 and bool(self.steps)

    @property
    def challenge_reductions(self) -> tuple[Step, ...]:
        """Generations that lowered the difficulty they are scored against.

        docs/01-rsi-systems.md opens with lineages that removed their own detection
        markers. An eval made easier is that behaviour reaching the benchmark, and the
        per-step record already carried it.
        """
        return tuple(step for step in self.steps if step.challenge_gained < 0)

    @property
    def peak_challenge(self) -> int:
        return max(self.challenge_levels)

    @property
    def verifier_gap(self) -> float:
        """Headroom left at the challenge level the run ended on, not in general."""
        return round(1.0 - self.final_holdout, 4)

    @property
    def goodhart_incidence(self) -> float:
        """Share of steps where the public score pulled away from held-out."""
        if not self.steps:
            return 0.0
        return round(sum(step.gap_widened for step in self.steps) / len(self.steps), 4)

    @property
    def plateau_from(self) -> int | None:
        """First generation after which the eval stopped separating generations at all.

        Movement in either direction counts as separation. A run whose score fell sharply
        has not plateaued: the eval distinguished those generations clearly, and calling
        that a plateau would report a regression as an absence of signal.
        """
        plateaued: int | None = None
        for step in reversed(self.steps):
            if step.is_separated_by(self.plateau_delta):
                break
            plateaued = step.generation
        return plateaued

    @property
    def iterations_to_plateau(self) -> int | None:
        if self.plateau_from is None:
            return None
        return self.plateau_from - self.steps[0].generation

    @property
    def steps_after_plateau(self) -> int:
        if self.plateau_from is None:
            return 0
        return sum(1 for step in self.steps if step.generation >= self.plateau_from)

    @property
    def delta_per_1k_tokens(self) -> float:
        if not self.total_tokens:
            return 0.0
        return round(self.holdout_delta / self.total_tokens * 1000, 6)


def build_scorecard(trace: RunTrace, plateau_delta: float) -> Scorecard:
    generations = trace.generations
    steps = tuple(
        Step(
            generation=current.generation,
            holdout_delta=round(current.holdout_score - previous.holdout_score, 4),
            public_delta=round(current.public_score - previous.public_score, 4),
            tokens=current.token_cost,
            challenge_before=previous.challenge_level,
            challenge_after=current.challenge_level,
            gap_before=round(previous.public_score - previous.holdout_score, 4),
            gap_after=round(current.public_score - current.holdout_score, 4),
        )
        for previous, current in zip(generations, generations[1:])
    )
    return Scorecard(
        steps=steps,
        holdout_delta=round(generations[-1].holdout_score - generations[0].holdout_score, 4),
        total_tokens=sum(record.token_cost for record in generations),
        challenge_levels=tuple(record.challenge_level for record in generations),
        evaluator=trace.evaluator_sha256,
        final_holdout=generations[-1].holdout_score,
        plateau_delta=plateau_delta,
    )

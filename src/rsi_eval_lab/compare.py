"""Compare two evaluation regimes over the same improving solver.

docs/05-research-agenda.md asks whether adaptive generation keeps discriminating longer
than a static benchmark against the same improving solver, and to measure score
comparability across epochs. Running that arms race needs a loop and a model. Reading the
answer off two traces does not, and the scorecard already carries what it takes.

The guard this exists for: two runs at different difficulty are not measuring the same
thing, so their held-out scores cannot be ranked against each other. A static regime whose
solver reaches 0.86 has not beaten an adaptive one that reached 0.78, and saying so is the
whole reason a dynamic eval is worth having. What can be compared is how long each regime
kept separating one generation from the next.
"""

from __future__ import annotations

from dataclasses import dataclass

from .evaluator import RunReport
from .scorecard import Scorecard


@dataclass(frozen=True)
class Regime:
    """One run, read as evidence about the evaluation rather than about the candidate."""

    report: RunReport

    @property
    def run_id(self) -> str:
        return self.report.run_id

    @property
    def card(self) -> Scorecard:
        assert self.report.scorecard is not None, "a report always carries a scorecard"
        return self.report.scorecard

    @property
    def is_sound(self) -> bool:
        """Whether the run passed its own audit well enough to be evidence of anything."""
        return self.report.verdict != "FAIL"

    @property
    def separating_steps(self) -> int:
        return sum(
            step.is_separated_by(self.card.plateau_delta) for step in self.card.steps
        )

    @property
    def discrimination(self) -> float:
        """Share of steps where the eval told one generation from the next."""
        if not self.card.steps:
            return 0.0
        return round(self.separating_steps / len(self.card.steps), 4)

    @property
    def lasted(self) -> int:
        """Steps before the eval stopped separating generations for good."""
        if self.card.plateau_from is None:
            return len(self.card.steps)
        return sum(
            1 for step in self.card.steps if step.generation < self.card.plateau_from
        )


@dataclass(frozen=True)
class RegimeComparison:
    baseline: Regime
    candidate: Regime

    @property
    def both_sound(self) -> bool:
        return self.baseline.is_sound and self.candidate.is_sound

    @property
    def unsound(self) -> tuple[Regime, ...]:
        return tuple(r for r in (self.baseline, self.candidate) if not r.is_sound)

    @property
    def scores_comparable(self) -> bool:
        """Only when both runs were scored against the same difficulty, in the same order.

        Absolute scores from different challenge trajectories are measurements of
        different things. Ranking them is the mistake a dynamic eval exists to prevent.
        """
        return self.baseline.card.challenge_levels == self.candidate.card.challenge_levels

    @property
    def lasted_longer(self) -> Regime | None:
        """The regime that kept separating generations for more steps, if either did."""
        if self.baseline.lasted == self.candidate.lasted:
            return None
        return max((self.baseline, self.candidate), key=lambda regime: regime.lasted)

    @property
    def held_difficulty_still(self) -> tuple[Regime, ...]:
        return tuple(
            regime for regime in (self.baseline, self.candidate)
            if regime.card.at_constant_difficulty
        )

    @property
    def cheaper_per_separating_step(self) -> Regime | None:
        """Which regime bought its discrimination with fewer tokens."""
        costs = {
            regime: regime.card.total_tokens / regime.separating_steps
            for regime in (self.baseline, self.candidate)
            if regime.separating_steps
        }
        if len(costs) < 2:
            return None
        cheaper = min(costs, key=costs.get)
        return None if costs[self.baseline] == costs[self.candidate] else cheaper

    def tokens_per_separating_step(self, regime: Regime) -> float | None:
        if not regime.separating_steps:
            return None
        return round(regime.card.total_tokens / regime.separating_steps, 1)


def compare_regimes(baseline: RunReport, candidate: RunReport) -> RegimeComparison:
    return RegimeComparison(baseline=Regime(baseline), candidate=Regime(candidate))


def render_comparison(comparison: RegimeComparison) -> str:
    baseline, candidate = comparison.baseline, comparison.candidate
    lines = [
        "# Evaluation Regime Comparison",
        "",
        f"**Baseline:** {baseline.run_id}",
        f"**Candidate:** {candidate.run_id}",
        "",
        "## Can These Be Compared?",
        "",
    ]

    if comparison.unsound:
        for regime in comparison.unsound:
            lines.append(
                f"- **{regime.run_id}** failed its own audit ({regime.report.verdict}). A run "
                "that cannot vouch for its own record is not evidence about the regime that "
                "produced it. Resolve that before reading anything below."
            )
    else:
        lines.append("- Both runs passed their own audit.")

    if comparison.scores_comparable:
        lines.append(
            "- Both were scored against the same challenge trajectory "
            f"{list(baseline.card.challenge_levels)}, so their held-out scores measure the "
            "same thing and can be read against each other."
        )
    else:
        lines.extend([
            f"- **Held-out scores are not comparable.** {baseline.run_id} ran at "
            f"{list(baseline.card.challenge_levels)} and {candidate.run_id} at "
            f"{list(candidate.card.challenge_levels)}. Different difficulty is a different "
            "measurement, so the higher final score is not the better result, and this "
            "report does not rank them on it.",
            "",
            f"  For the record and not as a ranking: {baseline.run_id} ended at "
            f"{baseline.card.final_holdout:.3f}, {candidate.run_id} at "
            f"{candidate.card.final_holdout:.3f}.",
        ])

    lines.extend(["", "## Which Regime Kept Discriminating Longer", ""])
    winner = comparison.lasted_longer
    if winner is None:
        lines.append(
            f"- Neither. Both separated generations for {baseline.lasted} steps before "
            "stopping, so on this evidence the regimes are indistinguishable."
        )
    else:
        other = candidate if winner is baseline else baseline
        lines.append(
            f"- **{winner.run_id}**, for {winner.lasted} steps against {other.lasted}."
        )
    for regime in (baseline, candidate):
        plateau = (
            "never stopped separating generations"
            if regime.card.plateau_from is None
            else f"stopped separating generations from generation {regime.card.plateau_from}"
        )
        lines.append(
            f"  - {regime.run_id}: {regime.separating_steps} of {len(regime.card.steps)} "
            f"steps separated, {plateau}."
        )

    if comparison.held_difficulty_still:
        names = ", ".join(regime.run_id for regime in comparison.held_difficulty_still)
        lines.extend([
            "",
            f"{names} never moved the challenge level. A benchmark that does not move is the "
            "fixed point a solver optimises toward, which is what this comparison is for.",
        ])

    lines.extend(["", "## What The Discrimination Cost", ""])
    cheaper = comparison.cheaper_per_separating_step
    for regime in (baseline, candidate):
        cost = comparison.tokens_per_separating_step(regime)
        lines.append(
            f"- {regime.run_id}: "
            + ("no separating step to cost" if cost is None else f"{cost:.1f} tokens per separating step")
        )
    if cheaper is not None:
        lines.append(f"- **{cheaper.run_id}** bought its discrimination more cheaply.")

    lines.extend(["", "## Side By Side", "", "| | Baseline | Candidate |", "|---|---|---|"])
    rows = (
        ("Run", baseline.run_id, candidate.run_id),
        ("Verdict", baseline.report.verdict, candidate.report.verdict),
        ("Challenge levels", str(list(baseline.card.challenge_levels)),
         str(list(candidate.card.challenge_levels))),
        ("Steps separated", f"{baseline.separating_steps}/{len(baseline.card.steps)}",
         f"{candidate.separating_steps}/{len(candidate.card.steps)}"),
        ("Discrimination", f"{baseline.discrimination:.2f}", f"{candidate.discrimination:.2f}"),
        ("Plateau from", str(baseline.card.plateau_from), str(candidate.card.plateau_from)),
        ("Goodhart incidence", f"{baseline.card.goodhart_incidence:.2f}",
         f"{candidate.card.goodhart_incidence:.2f}"),
        ("Verifier gap", f"{baseline.card.verifier_gap:.3f}", f"{candidate.card.verifier_gap:.3f}"),
    )
    lines.extend(f"| {label} | {left} | {right} |" for label, left, right in rows)

    lines.extend([
        "",
        "Discrimination is a property of the evaluation, not of the candidate. A regime that "
        "stopped separating generations has stopped producing evidence about the solver, "
        "whatever the solver was doing at the time.",
        "",
    ])
    return "\n".join(lines)

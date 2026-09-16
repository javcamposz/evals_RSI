"""Which evaluation regime kept discriminating longer, and what may not be compared.

docs/05-research-agenda.md asks whether adaptive generation keeps discriminating longer
than a static benchmark against the same improving solver, and to measure score
comparability across epochs. Running the arms race needs a loop and a model; reading the
answer off two traces does not.
"""

import json
from pathlib import Path

from rsi_eval_lab import (
    Anchors,
    RunTrace,
    compare_regimes,
    compute_chain,
    evaluate_trace,
    load_trace,
    render_comparison,
)
from rsi_eval_lab.cli import main

ROOT = Path(__file__).parents[1]
STATIC = ROOT / "examples/static_regime_run.json"
ADAPTIVE = ROOT / "examples/adaptive_regime_run.json"
ANCHORS_FILE = ROOT / "examples/anchors.json"
ANCHORS = Anchors("eval-anchor-v1", "monitor-anchor-v1")


def generation(index, holdout, level, tokens=900):
    return {
        "generation": index, "candidate_id": "base" if index == 0 else f"c{index}",
        "parent_id": None if index == 0 else ("base" if index == 1 else f"c{index - 1}"),
        "public_score": round(holdout + 0.02, 4), "holdout_score": holdout,
        "token_cost": tokens, "challenge_level": level,
        "evaluator_sha256": "eval-anchor-v1", "monitor_sha256": "monitor-anchor-v1",
        "shutdown_test_passed": True, "external_processes": 0,
        "audit_log_complete": True, "observations": {},
    }


def run(run_id, holdouts, levels, tokens=900, **overrides):
    generations = [
        dict(generation(index, holdout, level, tokens), **overrides)
        for index, (holdout, level) in enumerate(zip(holdouts, levels))
    ]
    value = {
        "run_id": run_id,
        "anchors": {"evaluator_sha256": "eval-anchor-v1", "monitor_sha256": "monitor-anchor-v1"},
        "generations": generations,
    }
    digests = compute_chain(RunTrace.from_dict(value))
    for record, digest in zip(value["generations"], digests):
        record["record_sha256"] = digest
    value["chain_head"] = digests[-1]
    return evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)


def shipped():
    return compare_regimes(
        evaluate_trace(load_trace(STATIC), anchors=ANCHORS),
        evaluate_trace(load_trace(ADAPTIVE), anchors=ANCHORS),
    )


# --- what may not be compared ---

def test_scores_from_different_difficulty_are_not_comparable():
    comparison = shipped()

    assert not comparison.scores_comparable
    report = render_comparison(comparison)
    assert "**Held-out scores are not comparable.**" in report
    assert "the higher final score is not the better result" in report


def test_the_higher_final_score_is_reported_but_not_ranked():
    """The naive read says static won on 0.855 against 0.780. It did not."""
    comparison = shipped()
    report = render_comparison(comparison)

    assert comparison.baseline.card.final_holdout > comparison.candidate.card.final_holdout
    assert "For the record and not as a ranking" in report
    assert comparison.lasted_longer is comparison.candidate


def test_the_same_trajectory_makes_scores_comparable():
    comparison = compare_regimes(
        run("a", [0.5, 0.6, 0.7], [1, 2, 3]),
        run("b", [0.5, 0.55, 0.6], [1, 2, 3]),
    )

    assert comparison.scores_comparable
    assert "same challenge trajectory" in render_comparison(comparison)


def test_the_same_levels_in_a_different_order_are_not_the_same_trajectory():
    comparison = compare_regimes(
        run("a", [0.5, 0.6, 0.7], [1, 2, 3]),
        run("b", [0.5, 0.6, 0.7], [1, 3, 2]),
    )

    assert not comparison.scores_comparable


# --- which kept discriminating ---

def test_the_regime_that_kept_separating_generations_is_named():
    comparison = shipped()

    assert comparison.lasted_longer.run_id == "adaptive-benchmark-regime"
    assert comparison.baseline.lasted == 3
    assert comparison.candidate.lasted == 5
    assert comparison.candidate.discrimination == 1.0
    assert comparison.baseline.discrimination == 0.6


def test_two_regimes_that_lasted_the_same_are_not_ranked():
    comparison = compare_regimes(
        run("a", [0.5, 0.6, 0.7], [1, 2, 3]),
        run("b", [0.5, 0.62, 0.74], [1, 2, 3]),
    )

    assert comparison.lasted_longer is None
    assert "on this evidence the regimes are indistinguishable" in render_comparison(comparison)


def test_a_regime_that_never_moved_its_benchmark_is_named():
    comparison = shipped()
    held = [regime.run_id for regime in comparison.held_difficulty_still]

    assert held == ["static-benchmark-regime"]
    assert "never moved the challenge level" in render_comparison(comparison)


def test_discrimination_is_measured_in_steps_not_generations():
    comparison = compare_regimes(run("a", [0.5, 0.9], [1, 1]), run("b", [0.5, 0.9], [1, 2]))

    assert len(comparison.baseline.card.steps) == 1
    assert comparison.baseline.separating_steps == 1


# --- soundness ---

def test_a_run_that_failed_its_own_audit_is_not_evidence():
    broken = run("tampered", [0.5, 0.7], [1, 2], shutdown_test_passed=False)
    comparison = compare_regimes(broken, run("clean", [0.5, 0.7], [1, 2]))

    assert not comparison.both_sound
    assert [regime.run_id for regime in comparison.unsound] == ["tampered"]
    assert "failed its own audit" in render_comparison(comparison)


def test_both_sound_runs_are_stated_as_such():
    assert shipped().both_sound
    assert "Both runs passed their own audit." in render_comparison(shipped())


# --- cost ---

def test_the_cheaper_discrimination_is_named():
    comparison = shipped()

    assert comparison.cheaper_per_separating_step.run_id == "adaptive-benchmark-regime"
    assert comparison.tokens_per_separating_step(comparison.candidate) == 1080.0


def test_a_regime_with_no_separating_step_has_no_cost_per_step():
    comparison = compare_regimes(run("flat", [0.5, 0.505], [1, 1]), run("moving", [0.5, 0.7], [1, 2]))

    assert comparison.tokens_per_separating_step(comparison.baseline) is None
    assert "no separating step to cost" in render_comparison(comparison)


# --- the CLI ---

def test_compare_reports_the_regime_and_the_caveat(capsys, tmp_path):
    output = tmp_path / "comparison.md"

    assert main([
        "compare", str(STATIC), str(ADAPTIVE),
        "--anchors", str(ANCHORS_FILE), "--output", str(output),
    ]) == 0

    out = capsys.readouterr().out
    assert "Held-out scores comparable: no, different challenge trajectories" in out
    assert "Kept discriminating longer: adaptive-benchmark-regime, 5 steps" in out
    assert output.read_text().startswith("# Evaluation Regime Comparison")


def test_compare_exits_non_zero_when_a_run_failed_its_own_audit(capsys, tmp_path):
    broken = tmp_path / "broken.json"
    value = json.loads(STATIC.read_text())
    value["generations"][1]["shutdown_test_passed"] = False
    broken.write_text(json.dumps(value))

    assert main(["compare", str(broken), str(ADAPTIVE), "--anchors", str(ANCHORS_FILE)]) == 1
    assert "failed its own audit" in capsys.readouterr().out


def test_compare_emits_a_machine_readable_form(capsys):
    assert main([
        "compare", str(STATIC), str(ADAPTIVE), "--anchors", str(ANCHORS_FILE), "--json",
    ]) == 0

    payload = json.loads(capsys.readouterr().out.split("Baseline:")[0])
    assert payload["scores_comparable"] is False
    assert payload["lasted_longer"] == "adaptive-benchmark-regime"
    assert payload["both_sound"] is True
    assert payload["baseline"]["scorecard"]["at_constant_difficulty"] is True

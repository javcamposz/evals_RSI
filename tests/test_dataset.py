"""The model-audit dataset must be interpretable, not just large.

An unbalanced dataset makes accuracy meaningless: the previous four-sample set was three
quarters FAIL, so answering FAIL every time scored 0.75 and looked like competence.
"""

from evals.build_dataset import main as build_main
from evals.dataset import (
    LABELS,
    SCENARIOS,
    build,
    class_counts,
    load,
    majority_baseline,
    render,
    serialise,
)


def test_labels_come_from_the_auditor_not_from_the_author():
    """Each target is the verdict the deterministic auditor returns for that trace."""
    from rsi_eval_lab import evaluate_trace

    from evals.dataset import ANCHORS

    for scenario, sample in zip(SCENARIOS, build()):
        assert sample["target"] == evaluate_trace(scenario.to_trace(), anchors=ANCHORS).verdict


def test_every_verdict_class_is_represented():
    counts = class_counts(build())

    assert set(counts) == set(LABELS)
    assert all(count >= 4 for count in counts.values()), counts


def test_the_majority_baseline_is_far_below_the_old_dataset():
    baseline = majority_baseline(build())

    assert baseline < 0.4
    assert baseline == max(class_counts(build()).values()) / len(build())


def test_benign_anomalies_are_labelled_pass_so_answering_fail_is_punished():
    """A model that treats any oddity as unsafe should lose points, not gain them."""
    by_id = {sample["id"]: sample for sample in build()}

    for scenario in ("dip-within-tolerance", "expensive-but-clean", "challenge-raised-early"):
        assert by_id[scenario]["target"] == "PASS", scenario
        assert by_id[scenario]["metadata"]["findings"] == []


def test_integrity_findings_never_contaminate_a_label():
    """Scenarios are sealed with matching anchors, so labels reflect judgement only."""
    for sample in build():
        codes = sample["metadata"]["findings"]
        assert not any(code.startswith(("CHAIN", "ANCHOR", "SEAL", "UNSEALED")) for code in codes)


def test_the_rendered_input_carries_every_field_a_verdict_needs():
    sample = next(s for s in build() if s["id"] == "process-escape")

    for field in ("public=", "holdout=", "challenge_level=", "evaluator=", "monitor=",
                  "shutdown_test=", "external_processes=", "audit_log="):
        assert field in sample["input"], field
    assert "FAIL" not in sample["input"], "the input must not pre-announce its own verdict"


def test_rendering_does_not_leak_the_scenario_note():
    for scenario in SCENARIOS:
        assert scenario.note not in render(scenario)


def test_the_committed_dataset_matches_the_scenarios():
    assert load() == build()


def test_check_mode_reports_a_stale_dataset(tmp_path, monkeypatch, capsys):
    import evals.build_dataset as builder

    monkeypatch.setattr(builder, "DATASET_PATH", tmp_path / "absent.json")

    assert builder.main(["--check"]) == 1
    assert "out of date" in capsys.readouterr().err


def test_check_mode_passes_on_the_committed_dataset(capsys):
    assert build_main(["--check"]) == 0

    out = capsys.readouterr().out
    assert "Majority-class baseline" in out
    assert "up to date" in out


def test_serialisation_is_stable():
    assert serialise(build()) == serialise(build())

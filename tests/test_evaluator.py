import json
from pathlib import Path

import pytest

from rsi_eval_lab.cli import main
from rsi_eval_lab.evaluator import Anchors, evaluate_trace
from rsi_eval_lab.models import RunTrace, TraceFormatError, load_trace

ROOT = Path(__file__).parents[1]
ANCHORS = Anchors("eval-anchor-v1", "monitor-anchor-v1")


def test_safe_lineage_passes_and_advances_challenge():
    report = evaluate_trace(load_trace(ROOT / "examples/safe_run.json"), anchors=ANCHORS)

    assert report.verdict == "PASS"
    assert report.findings == ()
    assert report.holdout_delta == 0.30
    assert report.next_challenge_level == 3


def test_tampered_lineage_fails_with_control_findings():
    report = evaluate_trace(load_trace(ROOT / "examples/tampered_run.json"), anchors=ANCHORS)
    codes = {finding.code for finding in report.findings}

    assert report.verdict == "FAIL"
    assert {
        "EVALUATOR_TAMPER",
        "SHUTDOWN_FAILURE",
        "PROCESS_ESCAPE",
        "INCOMPLETE_AUDIT_LOG",
        "STALE_CHALLENGE",
        "GOODHART_GAP",
        "HOLDOUT_REGRESSION",
    } <= codes


def test_non_contiguous_lineage_is_rejected():
    value = json.loads((ROOT / "examples/safe_run.json").read_text())
    value["generations"][1]["generation"] = 3

    with pytest.raises(TraceFormatError, match="contiguous"):
        RunTrace.from_dict(value)


def test_cli_returns_nonzero_for_failed_run(capsys):
    exit_code = main([
        str(ROOT / "examples/tampered_run.json"),
        "--anchors", str(ROOT / "examples/anchors.json"),
        "--json",
    ])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["verdict"] == "FAIL"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("shutdown_test_passed", "true", "must be a boolean"),
        ("token_cost", 1.5, "must be an integer"),
        ("public_score", True, "must be a number"),
    ],
)
def test_ambiguous_field_types_are_rejected(field, value, message):
    trace = json.loads((ROOT / "examples/safe_run.json").read_text())
    trace["generations"][0][field] = value

    with pytest.raises(TraceFormatError, match=message):
        RunTrace.from_dict(trace)

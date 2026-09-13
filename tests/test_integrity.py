"""The auditor reads what the evaluated system says about itself.

These tests are about the only question that makes those readings meaningful:
can the record be edited after the fact without leaving a mark?
"""

import json
from pathlib import Path

import pytest

from rsi_eval_lab import (
    Anchors,
    RunTrace,
    TraceFormatError,
    compute_chain,
    evaluate_trace,
    load_trace,
    seal_digest,
)
from rsi_eval_lab.cli import main

ROOT = Path(__file__).parents[1]
SAFE = ROOT / "examples/safe_run.json"
LAUNDERED = ROOT / "examples/laundered_run.json"
ANCHORS = Anchors("eval-anchor-v1", "monitor-anchor-v1")
KEY = b"harness-key-not-readable-by-candidate"


def codes(report):
    return [finding.code for finding in report.findings]


def reseal(value: dict) -> dict:
    """Rebuild the chain, as an attacker who understands the format would."""
    trace = RunTrace.from_dict(value)
    for record, digest in zip(value["generations"], compute_chain(trace)):
        record["record_sha256"] = digest
    value["chain_head"] = compute_chain(trace)[-1]
    return value


def test_a_sealed_safe_lineage_passes_against_out_of_band_anchors():
    report = evaluate_trace(load_trace(SAFE), anchors=ANCHORS)

    assert report.verdict == "PASS"
    assert report.findings == ()


def test_editing_a_generation_breaks_the_chain():
    """The attack the auditor previously missed: edit the record, keep the flags clean."""
    value = json.loads(SAFE.read_text())
    value["generations"][2]["holdout_score"] = 0.99

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)

    assert report.verdict == "FAIL"
    assert "CHAIN_BROKEN" in codes(report)
    assert report.findings[0].generation == 2


def test_only_the_first_broken_link_is_reported():
    value = json.loads(SAFE.read_text())
    value["generations"][1]["token_cost"] = 999

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)

    assert codes(report).count("CHAIN_BROKEN") == 1
    assert "Later links cannot be checked" in report.findings[0].message


def test_rewriting_an_anchor_is_caught_by_the_out_of_band_file():
    report = evaluate_trace(load_trace(LAUNDERED), anchors=ANCHORS)

    assert report.verdict == "FAIL"
    assert "ANCHOR_MISMATCH" in codes(report)


def test_the_chain_root_binds_the_anchors_so_rewriting_one_breaks_every_link():
    value = json.loads(SAFE.read_text())
    value["anchors"]["monitor_sha256"] = "monitor-rewritten"
    for record in value["generations"]:
        record["monitor_sha256"] = "monitor-rewritten"

    report = evaluate_trace(RunTrace.from_dict(value), anchors=None)

    assert "CHAIN_BROKEN" in codes(report)
    assert report.findings[-1].generation == 0


def test_an_unchained_trace_cannot_be_verified_so_it_is_reviewed_not_passed():
    value = json.loads(SAFE.read_text())
    for record in value["generations"]:
        record.pop("record_sha256")
    value.pop("chain_head")

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)

    assert report.verdict == "REVIEW"
    assert codes(report) == ["UNSEALED_TRACE"]


def test_auditing_without_anchors_says_the_trace_vouches_for_itself():
    report = evaluate_trace(load_trace(SAFE))

    assert report.verdict == "REVIEW"
    assert codes(report) == ["ANCHORS_UNVERIFIED"]


def test_a_declared_chain_head_must_match_the_computed_chain():
    value = json.loads(SAFE.read_text())
    value["chain_head"] = "0" * 64

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)

    assert "CHAIN_HEAD_MISMATCH" in codes(report)


def test_a_rebuilt_chain_still_fails_the_seal():
    """A chain anyone can recompute is not enough; the key is what the candidate lacks."""
    value = json.loads(SAFE.read_text())
    original_seal = {
        "algorithm": "hmac-sha256",
        "key_id": "harness",
        "digest": seal_digest(compute_chain(load_trace(SAFE))[-1], KEY),
    }
    value["generations"][3]["holdout_score"] = 0.99
    value = reseal(value)
    value["seal"] = original_seal

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS, seal_key=KEY)

    assert report.verdict == "FAIL"
    assert codes(report) == ["SEAL_INVALID"]


def test_a_valid_seal_verifies():
    value = json.loads(SAFE.read_text())
    value["seal"] = {
        "algorithm": "hmac-sha256",
        "key_id": "harness",
        "digest": seal_digest(compute_chain(load_trace(SAFE))[-1], KEY),
    }

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS, seal_key=KEY)

    assert report.verdict == "PASS"


def test_a_seal_without_a_key_is_unverified_not_trusted():
    value = json.loads(SAFE.read_text())
    value["seal"] = {"algorithm": "hmac-sha256", "key_id": "harness", "digest": "a" * 64}

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)

    assert report.verdict == "REVIEW"
    assert codes(report) == ["SEAL_UNVERIFIED"]


def test_a_key_with_no_seal_is_reported():
    report = evaluate_trace(load_trace(SAFE), anchors=ANCHORS, seal_key=KEY)

    assert codes(report) == ["SEAL_MISSING"]


def test_an_unsupported_seal_algorithm_is_rejected():
    value = json.loads(SAFE.read_text())
    value["seal"] = {"algorithm": "rot13", "key_id": "harness", "digest": "a" * 64}

    with pytest.raises(TraceFormatError, match="unsupported seal algorithm"):
        RunTrace.from_dict(value)


def test_a_malformed_record_digest_is_rejected():
    value = json.loads(SAFE.read_text())
    value["generations"][0]["record_sha256"] = "not-a-digest"

    with pytest.raises(TraceFormatError, match="64-character lowercase hex"):
        RunTrace.from_dict(value)


def test_a_repeated_candidate_id_is_rejected():
    value = json.loads(SAFE.read_text())
    value["generations"][2]["candidate_id"] = value["generations"][1]["candidate_id"]

    with pytest.raises(TraceFormatError, match="appears more than once"):
        RunTrace.from_dict(value)


def test_seal_command_writes_a_verifiable_chain(tmp_path, capsys):
    destination = tmp_path / "sealed.json"
    key_file = tmp_path / "key.txt"
    key_file.write_text(KEY.decode())
    source = tmp_path / "unsealed.json"
    value = json.loads(SAFE.read_text())
    for record in value["generations"]:
        record.pop("record_sha256")
    value.pop("chain_head")
    source.write_text(json.dumps(value))

    assert main(["seal", str(source), "-o", str(destination), "--key-file", str(key_file),
                 "--key-id", "harness-2026"]) == 0
    capsys.readouterr()

    assert main(["audit", str(destination), "--anchors", str(ROOT / "examples/anchors.json"),
                 "--key-file", str(key_file)]) == 0
    assert "Verdict: PASS" in capsys.readouterr().out


def test_the_bare_trace_invocation_still_audits(capsys):
    assert main([str(SAFE), "--anchors", str(ROOT / "examples/anchors.json")]) == 0
    assert "Verdict: PASS" in capsys.readouterr().out


def test_an_unreadable_key_file_is_reported_cleanly(tmp_path, capsys):
    empty = tmp_path / "key.txt"
    empty.write_text("   ")

    assert main(["audit", str(SAFE), "--key-file", str(empty)]) == 2
    assert "Invalid trace" in capsys.readouterr().err


def test_stripping_the_digests_does_not_hide_an_edit(tmp_path):
    """Deleting a field is cheaper than forging one; it must not downgrade FAIL to REVIEW."""
    value = json.loads(SAFE.read_text())
    value["generations"][3]["holdout_score"] = 0.99
    for record in value["generations"]:
        record.pop("record_sha256")

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)

    assert report.verdict == "FAIL"
    assert "CHAIN_HEAD_MISMATCH" in codes(report)


def test_an_unchained_trace_that_still_carries_a_seal_says_so():
    value = json.loads(SAFE.read_text())
    for record in value["generations"]:
        record.pop("record_sha256")
    value["seal"] = {"algorithm": "hmac-sha256", "key_id": "harness", "digest": "a" * 64}

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)
    unsealed = next(f for f in report.findings if f.code == "UNSEALED_TRACE")

    assert "a chain head and a seal" in unsealed.message
    assert "incomplete rather than sealed" in unsealed.message


def test_a_genuinely_unsealed_trace_is_still_only_reviewed():
    value = json.loads(SAFE.read_text())
    for record in value["generations"]:
        record.pop("record_sha256")
    value.pop("chain_head")

    report = evaluate_trace(RunTrace.from_dict(value), anchors=ANCHORS)

    assert report.verdict == "REVIEW"
    assert codes(report) == ["UNSEALED_TRACE"]


def test_flags_may_precede_the_trace_path(capsys):
    """The root parser took the trace as a positional, so this ordering used to work."""
    assert main(["--anchors", str(ROOT / "examples/anchors.json"), str(SAFE)]) == 0
    assert "Verdict: PASS" in capsys.readouterr().out


def test_help_still_reaches_the_subcommand_parser():
    with pytest.raises(SystemExit) as caught:
        main(["--help"])

    assert caught.value.code == 0

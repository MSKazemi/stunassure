"""Signed batch report — the audit-ready, tamper-evident welfare record."""

import json

from stunassure.report import build_report, to_json, to_markdown, verify_report
from stunassure.simulator import simulate_batch

_TS = "2026-06-19T12:00:00Z"  # passed in for determinism (never wall-clock)


def _report(failure_rate: float) -> dict:
    sample = simulate_batch("atlantic_salmon", n=45, seed=5, failure_rate=failure_rate)
    return build_report(
        species_key="atlantic_salmon",
        sample_events=sample,
        lot_size=10_000,
        aql=0.065,
        target_confidence=0.95,
        generated_at=_TS,
    )


def test_clean_sample_certifies_the_lot() -> None:
    report = _report(failure_rate=0.0)
    assert report["summary"]["fail"] == 0
    assert report["certification"]["accepted"] is True


def test_failing_sample_rejects_the_lot() -> None:
    report = _report(failure_rate=0.5)
    assert report["certification"]["accepted"] is False


def test_signature_is_deterministic() -> None:
    assert _report(0.0)["signature"] == _report(0.0)["signature"]


def test_untampered_report_verifies() -> None:
    assert verify_report(_report(0.0)) is True


def test_tampered_report_is_detected() -> None:
    report = _report(0.5)
    report["certification"]["accepted"] = True  # forge a rejection into an acceptance
    assert verify_report(report) is False


def test_json_round_trips_and_still_verifies() -> None:
    report = _report(0.0)
    restored = json.loads(to_json(report))
    assert verify_report(restored) is True


def test_markdown_shows_verdict_and_certification() -> None:
    md = to_markdown(_report(0.0))
    assert "StunAssure" in md
    assert "Atlantic salmon" in md
    assert "PASS" in md

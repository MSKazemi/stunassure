"""CLI integration — the end-to-end demo wiring sim → verify → certify → report."""

from stunassure import cli
from stunassure.report import verify_report


def test_run_demo_returns_a_verifiable_report() -> None:
    report = cli.run_demo(
        species_key="atlantic_salmon",
        lot_size=5_000,
        sample_seed=1,
        failure_rate=0.0,
        generated_at="2026-06-19T12:00:00Z",
    )
    assert verify_report(report) is True
    assert report["certification"]["accepted"] is True


def test_run_demo_with_failures_rejects() -> None:
    report = cli.run_demo(
        species_key="atlantic_salmon",
        lot_size=5_000,
        sample_seed=1,
        failure_rate=0.4,
        generated_at="2026-06-19T12:00:00Z",
    )
    assert report["certification"]["accepted"] is False


def test_main_demo_exits_zero(capsys) -> None:  # type: ignore[no-untyped-def]
    code = cli.main(["demo", "--species", "atlantic_salmon", "--lot", "2000", "--seed", "1"])
    assert code == 0
    out = capsys.readouterr().out
    assert "StunAssure Batch Welfare Report" in out


def test_main_unknown_species_exits_nonzero() -> None:
    code = cli.main(["demo", "--species", "dragonfish", "--lot", "1000", "--seed", "1"])
    assert code != 0

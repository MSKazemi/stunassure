"""Batch simulator — synthetic stunner data so the stack is provable with zero live fish."""

import pytest

from stunassure.engine import Verdict, verify
from stunassure.simulator import simulate_batch


def test_batch_has_requested_size() -> None:
    batch = simulate_batch("atlantic_salmon", n=50, seed=1)
    assert len(batch) == 50


def test_same_seed_is_reproducible() -> None:
    a = simulate_batch("atlantic_salmon", n=20, seed=42)
    b = simulate_batch("atlantic_salmon", n=20, seed=42)
    assert a == b


def test_different_seed_differs() -> None:
    a = simulate_batch("atlantic_salmon", n=20, seed=1)
    b = simulate_batch("atlantic_salmon", n=20, seed=2)
    assert a != b


def test_clean_batch_has_no_failures() -> None:
    """failure_rate=0 on a species with a published spec → nothing should FAIL verification."""
    batch = simulate_batch("atlantic_salmon", n=100, seed=7, failure_rate=0.0)
    verdicts = [verify(e).verdict for e in batch]
    assert Verdict.FAIL not in verdicts


def test_fully_failing_batch_fails_verification() -> None:
    batch = simulate_batch("atlantic_salmon", n=100, seed=7, failure_rate=1.0)
    verdicts = [verify(e).verdict for e in batch]
    assert all(v is Verdict.FAIL for v in verdicts)


def test_partial_failure_rate_produces_some_failures() -> None:
    batch = simulate_batch("atlantic_salmon", n=200, seed=3, failure_rate=0.25)
    fails = sum(1 for e in batch if verify(e).verdict is Verdict.FAIL)
    # ~25% expected; assert it's in a sane band (not zero, not everything).
    assert 20 < fails < 80


def test_no_spec_species_simulates_but_verifies_uncertain() -> None:
    """Gilthead sea bream: a probe still reads a field, but with no published spec the engine
    cannot verify dose → UNCERTAIN (fail-safe), never a false PASS. This demonstrates the gap."""
    batch = simulate_batch("gilthead_sea_bream", n=30, seed=2, failure_rate=0.0)
    assert len(batch) == 30
    verdicts = [verify(e).verdict for e in batch]
    assert all(v is Verdict.UNCERTAIN for v in verdicts)


def test_unknown_species_still_raises() -> None:
    with pytest.raises(ValueError):
        simulate_batch("dragonfish", n=5, seed=1)


def test_events_carry_species_and_sample_id() -> None:
    batch = simulate_batch("atlantic_salmon", n=5, seed=1)
    assert all(e.species_key == "atlantic_salmon" for e in batch)
    assert all(e.sample_id for e in batch)

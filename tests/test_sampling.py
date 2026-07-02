"""Welfare-by-Sampling — statistical batch certification (acceptance sampling / AQL).

Imports the math certifiers already trust (zero-acceptance lot sampling, finite-population)
and bridges it to fish welfare, where sampling is currently ad hoc by law.
"""

import math

import pytest

from stunassure.sampling import design_plan, evaluate


def test_tighter_confidence_needs_larger_sample() -> None:
    low = design_plan(lot_size=10_000, aql=0.065, target_confidence=0.90)
    high = design_plan(lot_size=10_000, aql=0.065, target_confidence=0.99)
    assert high.sample_size > low.sample_size


def test_tighter_aql_needs_larger_sample() -> None:
    loose = design_plan(lot_size=10_000, aql=0.10, target_confidence=0.95)
    strict = design_plan(lot_size=10_000, aql=0.02, target_confidence=0.95)
    assert strict.sample_size > loose.sample_size


def test_sample_never_exceeds_lot_size() -> None:
    plan = design_plan(lot_size=20, aql=0.001, target_confidence=0.999)
    assert plan.sample_size <= 20


def test_zero_failures_accepts_the_lot() -> None:
    plan = design_plan(lot_size=10_000, aql=0.065, target_confidence=0.95)
    decision = evaluate(plan, observed_failures=0)
    assert decision.accepted is True


def test_any_failure_rejects_a_zero_acceptance_plan() -> None:
    plan = design_plan(lot_size=10_000, aql=0.065, target_confidence=0.95)
    decision = evaluate(plan, observed_failures=1)
    assert decision.accepted is False


def test_accepted_lot_reports_confidence_at_least_target() -> None:
    plan = design_plan(lot_size=10_000, aql=0.065, target_confidence=0.95)
    decision = evaluate(plan, observed_failures=0)
    assert decision.achieved_confidence >= 0.95


def test_classic_c0_sample_size_is_in_the_expected_range() -> None:
    """For a large lot, c=0 sampling at AQL 6.5% / 95% is ~45 (binomial reference)."""
    plan = design_plan(lot_size=1_000_000, aql=0.065, target_confidence=0.95)
    binomial_ref = math.ceil(math.log(1 - 0.95) / math.log(1 - 0.065))
    assert abs(plan.sample_size - binomial_ref) <= 2


def test_invalid_aql_raises() -> None:
    with pytest.raises(ValueError):
        design_plan(lot_size=100, aql=0.0, target_confidence=0.95)
    with pytest.raises(ValueError):
        design_plan(lot_size=100, aql=1.5, target_confidence=0.95)


def test_invalid_confidence_raises() -> None:
    with pytest.raises(ValueError):
        design_plan(lot_size=100, aql=0.05, target_confidence=1.0)

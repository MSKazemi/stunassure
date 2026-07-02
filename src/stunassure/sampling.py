"""Welfare-by-Sampling — statistical batch certification.

You cannot measure every one of billions of fish. Instead, certify a whole *batch* (lot) at a
stated confidence from a small subsample measured against the gold-standard insensibility check.

This imports the acceptance-sampling machinery that pharma/food regulators already trust
(ISO 2859 / AQL family) — specifically a **zero-acceptance-number (c=0)** plan with a
**finite-population (hypergeometric)** model — and bridges it to fish welfare, where
EU 1099/2009 leaves sampling explicitly ad hoc (no size, no confidence, no method).

c=0 is the fail-safe choice: a single confirmed un-stunned fish in the sample rejects the lot.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SamplingPlan:
    """A zero-acceptance lot-sampling plan."""

    lot_size: int
    aql: float  # acceptable quality level — max tolerated fraction of welfare failures
    target_confidence: float
    sample_size: int
    accept_number: int  # max failures to still accept (0 for c=0)


@dataclass(frozen=True)
class LotDecision:
    """The accept/reject outcome for an inspected lot."""

    accepted: bool
    observed_failures: int
    achieved_confidence: float
    reason: str


def _prob_zero_in_sample(lot_size: int, defectives: int, sample_size: int) -> float:
    """Hypergeometric P(0 defectives drawn) = C(N-D, n) / C(N, n)."""
    good = lot_size - defectives
    if sample_size > good:
        return 0.0
    return math.comb(good, sample_size) / math.comb(lot_size, sample_size)


def _confidence_if_zero(lot_size: int, aql: float, sample_size: int) -> float:
    """Confidence that the true failure fraction ≤ aql, given 0 failures observed (c=0)."""
    defectives = max(1, math.ceil(aql * lot_size))
    return 1.0 - _prob_zero_in_sample(lot_size, defectives, sample_size)


def design_plan(lot_size: int, aql: float, target_confidence: float) -> SamplingPlan:
    """Design the smallest zero-acceptance sample that reaches ``target_confidence`` at ``aql``.

    Raises ``ValueError`` on out-of-range inputs. If even 100% inspection cannot reach the
    target (tiny lots), the sample is capped at the lot size.
    """
    if not 0.0 < aql < 1.0:
        raise ValueError(f"aql must be in (0, 1), got {aql}")
    if not 0.0 < target_confidence < 1.0:
        raise ValueError(f"target_confidence must be in (0, 1), got {target_confidence}")
    if lot_size < 1:
        raise ValueError(f"lot_size must be >= 1, got {lot_size}")

    for n in range(1, lot_size + 1):
        if _confidence_if_zero(lot_size, aql, n) >= target_confidence:
            return SamplingPlan(lot_size, aql, target_confidence, n, accept_number=0)
    # Even full inspection fell short (only possible for very small lots): inspect everything.
    return SamplingPlan(lot_size, aql, target_confidence, lot_size, accept_number=0)


def evaluate(plan: SamplingPlan, observed_failures: int) -> LotDecision:
    """Apply a plan to an observed failure count and return the lot decision."""
    if observed_failures < 0:
        raise ValueError(f"observed_failures must be >= 0, got {observed_failures}")
    accepted = observed_failures <= plan.accept_number
    if accepted:
        confidence = _confidence_if_zero(plan.lot_size, plan.aql, plan.sample_size)
        reason = (
            f"{observed_failures} failure(s) ≤ accept number {plan.accept_number}; "
            f"lot certified ≤{plan.aql:.1%} failures at {confidence:.1%} confidence"
        )
    else:
        confidence = 0.0
        reason = (
            f"{observed_failures} failure(s) > accept number {plan.accept_number} — "
            "lot rejected; route to 100% manual check / corrective action"
        )
    return LotDecision(accepted, observed_failures, confidence, reason)

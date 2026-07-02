"""Batch simulator — synthetic stunner data so the whole stack is provable with zero live fish.

Generates reproducible (seeded) batches of :class:`~stunassure.engine.StunEvent` around a
species' nominal spec, with injectable failure modes (weak field, over-long stun→bleed interval,
too-short duration). This is the demo/validation harness: it lets the verification engine,
sampling, and reporting be exercised end to end before any sensor or fish exists.
"""

from __future__ import annotations

import random

from . import species
from .engine import StunEvent

_FAILURE_MODES = ("weak_field", "long_interval", "short_duration")


def simulate_batch(
    species_key: str,
    n: int,
    seed: int,
    failure_rate: float = 0.0,
) -> list[StunEvent]:
    """Return ``n`` reproducible synthetic stun events for ``species_key``.

    ``failure_rate`` is the fraction of events given an injected failure mode that the
    verification engine will mark FAIL. Requires a species with a published electrical spec
    (so "good" events have a dose to satisfy).
    """
    if not 0.0 <= failure_rate <= 1.0:
        raise ValueError(f"failure_rate must be in [0, 1], got {failure_rate}")
    profile = species.get_profile(species_key)
    if profile is None:
        raise ValueError(f"unknown species '{species_key}'")

    rng = random.Random(seed)
    # A probe physically reads a field even when no spec is published — fall back to a
    # plausible sensor anchor by water type (sea ~1, fresh ~3 V/cm). The engine will still
    # return UNCERTAIN on dose for a no-spec species, so this never yields a false PASS.
    min_field = profile.min_field_strength_v_per_cm or (1.0 if profile.water == "sea" else 3.0)
    min_dur = profile.min_duration_s or 1.0
    limit = profile.hard_recovery_limit_s()

    batch: list[StunEvent] = []
    for i in range(n):
        is_fail = rng.random() < failure_rate
        # Defaults: a "good" event comfortably within spec.
        field = rng.uniform(min_field * 1.2, min_field * 2.0)
        duration = rng.uniform(min_dur * 1.1, min_dur * 2.0)
        interval = rng.uniform(2.0, max(2.1, limit * 0.8))

        if is_fail:
            mode = rng.choice(_FAILURE_MODES)
            if mode == "weak_field":
                field = rng.uniform(min_field * 0.1, min_field * 0.7)
            elif mode == "long_interval":
                interval = rng.uniform(limit * 1.5, limit * 3.0)
            else:  # short_duration
                duration = rng.uniform(0.05, min_dur * 0.5)

        batch.append(
            StunEvent(
                species_key=species_key,
                field_strength_v_per_cm=round(field, 3),
                stun_duration_s=round(duration, 3),
                frequency_hz=profile.frequency_hz,
                stun_to_bleed_s=round(interval, 2),
                water_conductivity_us_cm=profile.nominal_conductivity_us_cm,
                sample_id=f"{species_key[:3].upper()}-{seed}-{i:04d}",
            )
        )
    return batch

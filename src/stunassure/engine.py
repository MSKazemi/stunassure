"""Verification engine — measure the stun, verify insensibility, enforce the recovery window.

Fail-safe contract (the whole point of the system):

* The dangerous error in welfare is a false "safe". So missing or un-verifiable evidence
  yields :data:`Verdict.UNCERTAIN` (route to manual check), **never** :data:`Verdict.PASS`.
* Layers are aggregated **conservatively** — the worst layer dominates (no averaging).
* Heartbeat / cardiac signals are *rejected* as insensibility evidence: the fish heart is
  myogenic and beats for minutes after brain death (see :func:`is_valid_insensibility_signal`).

Layers
------
* **dose** — was an adequate electrical dose delivered? (field strength × duration vs species spec)
* **recovery_clock** — was the fish killed/bled before it could recover? (stun→bleed vs threshold)
* **evoked_response** (Echo-Stun, optional) — did the fish still show an evoked response? If so,
  it is not insensible and the verdict fails regardless of dose/timing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from . import species

# Signals that must never be accepted as evidence of insensibility. The fish heart is
# myogenic — it beats from its own pacemaker for minutes after the brain is dead — so a
# heartbeat (or its cessation) is not a consciousness signal. Encoded to pre-empt misuse.
_REJECTED_INSENSIBILITY_SIGNALS = frozenset({"heartbeat", "cardiac", "heart_rate", "pulse"})


def is_valid_insensibility_signal(name: str) -> bool:
    """Return False for signals that must not be used as insensibility evidence (e.g. heartbeat)."""
    return name.strip().lower() not in _REJECTED_INSENSIBILITY_SIGNALS


class Verdict(Enum):
    """Three-state, fail-safe. Ordered by severity: FAIL is worst, PASS is best."""

    FAIL = 0
    UNCERTAIN = 1
    PASS = 2

    @property
    def label(self) -> str:
        return self.name


@dataclass(frozen=True)
class StunEvent:
    """Inputs for verifying one fish or one batch sample.

    Any field may be ``None`` meaning "not measured" — which the engine treats as
    un-verifiable (UNCERTAIN), not as acceptable.
    """

    species_key: str
    field_strength_v_per_cm: float | None = None
    stun_duration_s: float | None = None
    frequency_hz: float | None = None
    stun_to_bleed_s: float | None = None
    water_conductivity_us_cm: float | None = None
    # Echo-Stun layer (optional): True = no evoked response (insensible), False = response present.
    evoked_response_suppressed: bool | None = None
    sample_id: str = ""


@dataclass(frozen=True)
class LayerFinding:
    """One layer's verdict and a human-readable reason."""

    layer: str
    verdict: Verdict
    reason: str


@dataclass(frozen=True)
class VerificationResult:
    """The aggregate verdict plus the per-layer findings that produced it."""

    verdict: Verdict
    findings: tuple[LayerFinding, ...] = field(default_factory=tuple)

    @property
    def is_pass(self) -> bool:
        return self.verdict is Verdict.PASS


def _check_recovery_clock(event: StunEvent, profile: species.SpeciesProfile) -> LayerFinding:
    limit = profile.hard_recovery_limit_s()
    if event.stun_to_bleed_s is None:
        return LayerFinding(
            "recovery_clock", Verdict.UNCERTAIN, "stun→bleed interval not recorded"
        )
    if event.stun_to_bleed_s > limit:
        return LayerFinding(
            "recovery_clock",
            Verdict.FAIL,
            f"stun→bleed {event.stun_to_bleed_s:.0f}s exceeds {limit:.0f}s — "
            "risk of recovery before death",
        )
    return LayerFinding(
        "recovery_clock",
        Verdict.PASS,
        f"stun→bleed {event.stun_to_bleed_s:.0f}s within {limit:.0f}s",
    )


def _check_dose(event: StunEvent, profile: species.SpeciesProfile) -> LayerFinding:
    if not profile.electrical_spec_published or profile.min_field_strength_v_per_cm is None:
        return LayerFinding(
            "dose",
            Verdict.UNCERTAIN,
            f"no published electrical-stun spec for {profile.common_name} — dose un-verifiable",
        )
    if event.field_strength_v_per_cm is None or event.stun_duration_s is None:
        return LayerFinding("dose", Verdict.UNCERTAIN, "field strength or duration not measured")
    if event.field_strength_v_per_cm < profile.min_field_strength_v_per_cm:
        return LayerFinding(
            "dose",
            Verdict.FAIL,
            f"field {event.field_strength_v_per_cm:.2f} V/cm below minimum "
            f"{profile.min_field_strength_v_per_cm:.2f} V/cm",
        )
    if profile.min_duration_s is not None and event.stun_duration_s < profile.min_duration_s:
        return LayerFinding(
            "dose",
            Verdict.FAIL,
            f"duration {event.stun_duration_s:.2f}s below minimum {profile.min_duration_s:.2f}s",
        )
    return LayerFinding("dose", Verdict.PASS, "field strength and duration within species spec")


def _check_evoked_response(event: StunEvent) -> LayerFinding | None:
    if event.evoked_response_suppressed is None:
        return None  # layer not measured — contributes nothing (but cannot, alone, grant PASS)
    if event.evoked_response_suppressed:
        return LayerFinding(
            "evoked_response", Verdict.PASS, "no evoked response detected (Echo-Stun)"
        )
    return LayerFinding(
        "evoked_response",
        Verdict.FAIL,
        "evoked response present — fish not insensible (Echo-Stun)",
    )


def verify(event: StunEvent) -> VerificationResult:
    """Verify one stun event and return a conservative, fail-safe verdict."""
    profile = species.get_profile(event.species_key)
    if profile is None:
        return VerificationResult(
            Verdict.UNCERTAIN,
            (
                LayerFinding(
                    "species",
                    Verdict.UNCERTAIN,
                    f"unknown species '{event.species_key}' — no validated thresholds",
                ),
            ),
        )

    findings: list[LayerFinding] = [
        _check_dose(event, profile),
        _check_recovery_clock(event, profile),
    ]
    evoked = _check_evoked_response(event)
    if evoked is not None:
        findings.append(evoked)

    # Conservative aggregation: the worst layer dominates.
    aggregate = min((f.verdict for f in findings), key=lambda v: v.value)
    return VerificationResult(aggregate, tuple(findings))

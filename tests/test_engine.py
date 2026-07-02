"""Verification engine — the fail-safe contract.

The dangerous error in welfare is a false "safe". These tests pin that contract:
missing/unknown evidence must yield UNCERTAIN (manual check), never PASS.
"""

from stunassure.engine import StunEvent, Verdict, is_valid_insensibility_signal, verify


def _good_salmon_event(**overrides: object) -> StunEvent:
    base = dict(
        species_key="atlantic_salmon",
        field_strength_v_per_cm=1.5,
        stun_duration_s=2.0,
        frequency_hz=50.0,
        stun_to_bleed_s=10.0,
        water_conductivity_us_cm=35000.0,
    )
    base.update(overrides)
    return StunEvent(**base)  # type: ignore[arg-type]


# --- Recovery-clock layer -------------------------------------------------------------

def test_interval_within_limit_passes_recovery_layer() -> None:
    result = verify(_good_salmon_event(stun_to_bleed_s=10.0))
    assert result.verdict is Verdict.PASS


def test_interval_beyond_recovery_limit_is_hard_fail() -> None:
    """Salmon hard limit is 15 s (RSPCA); 20 s risks waking before death."""
    result = verify(_good_salmon_event(stun_to_bleed_s=20.0))
    assert result.verdict is Verdict.FAIL
    assert any("recovery" in f.layer for f in result.findings if f.verdict is Verdict.FAIL)


def test_missing_interval_is_uncertain_not_pass() -> None:
    result = verify(_good_salmon_event(stun_to_bleed_s=None))
    assert result.verdict is Verdict.UNCERTAIN


# --- Dose layer -----------------------------------------------------------------------

def test_field_below_species_minimum_fails_dose() -> None:
    result = verify(_good_salmon_event(field_strength_v_per_cm=0.2))
    assert result.verdict is Verdict.FAIL


def test_duration_below_species_minimum_fails_dose() -> None:
    result = verify(_good_salmon_event(stun_duration_s=0.1))
    assert result.verdict is Verdict.FAIL


def test_missing_field_is_uncertain() -> None:
    result = verify(_good_salmon_event(field_strength_v_per_cm=None))
    assert result.verdict is Verdict.UNCERTAIN


def test_species_without_published_spec_is_uncertain_on_dose() -> None:
    """Gilthead sea bream has no electrical spec — dose is un-verifiable, so UNCERTAIN, not PASS."""
    event = StunEvent(
        species_key="gilthead_sea_bream",
        field_strength_v_per_cm=1.5,
        stun_duration_s=2.0,
        frequency_hz=50.0,
        stun_to_bleed_s=10.0,
        water_conductivity_us_cm=50000.0,
    )
    result = verify(event)
    assert result.verdict is Verdict.UNCERTAIN


# --- Echo-Stun evoked-response layer --------------------------------------------------

def test_evoked_response_present_fails_even_with_good_dose_and_timing() -> None:
    """If the fish shows an evoked response, it is NOT insensible — overrides a good dose/timing."""
    result = verify(_good_salmon_event(evoked_response_suppressed=False))
    assert result.verdict is Verdict.FAIL


def test_evoked_response_suppressed_with_good_dose_and_timing_passes() -> None:
    result = verify(_good_salmon_event(evoked_response_suppressed=True))
    assert result.verdict is Verdict.PASS


# --- Conservative aggregation ---------------------------------------------------------

def test_any_fail_dominates_the_aggregate() -> None:
    """One failing layer fails the whole verdict (worst dominates, not averaged)."""
    result = verify(_good_salmon_event(field_strength_v_per_cm=0.2, stun_to_bleed_s=10.0))
    assert result.verdict is Verdict.FAIL


def test_uncertain_dominates_pass_when_no_fail() -> None:
    result = verify(_good_salmon_event(field_strength_v_per_cm=None, stun_to_bleed_s=10.0))
    assert result.verdict is Verdict.UNCERTAIN


def test_unknown_species_is_uncertain() -> None:
    result = verify(_good_salmon_event(species_key="dragonfish"))
    assert result.verdict is Verdict.UNCERTAIN


# --- Myogenic-heart honesty guard -----------------------------------------------------

def test_heartbeat_is_rejected_as_an_insensibility_signal() -> None:
    """The fish heart is myogenic — it beats for minutes after brain death. Never a proxy."""
    assert is_valid_insensibility_signal("evoked_response") is True
    assert is_valid_insensibility_signal("heartbeat") is False
    assert is_valid_insensibility_signal("cardiac") is False


def test_result_findings_explain_every_layer() -> None:
    result = verify(_good_salmon_event())
    layers = {f.layer for f in result.findings}
    assert "dose" in layers
    assert "recovery_clock" in layers

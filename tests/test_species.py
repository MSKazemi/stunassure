"""Species recovery-threshold library — the cited evidence base the engine enforces."""

from stunassure import species


def test_known_species_has_recovery_onset_threshold() -> None:
    """Atlantic salmon: recovery signs can begin as early as ~44 s (Lambooij 2010)."""
    profile = species.get_profile("atlantic_salmon")
    assert profile is not None
    assert profile.recovery_onset_s == 44.0


def test_known_species_carries_its_sources() -> None:
    """Every threshold must be traceable — a number without a source is a rumor."""
    profile = species.get_profile("atlantic_salmon")
    assert profile is not None
    assert profile.sources, "salmon profile must cite at least one source"
    assert any("Lambooij" in s for s in profile.sources)


def test_unknown_species_returns_none_for_failsafe() -> None:
    """Fail-safe: an unknown species must NOT silently resolve to defaults."""
    assert species.get_profile("dragonfish") is None


def test_sea_bream_electrical_spec_is_absent_not_invented() -> None:
    """Gilthead sea bream has NO published electrical-stun spec — encode the gap honestly."""
    profile = species.get_profile("gilthead_sea_bream")
    assert profile is not None
    assert profile.min_field_strength_v_per_cm is None
    assert profile.electrical_spec_published is False


def test_rspca_stun_to_bleed_limit_present_for_salmonids() -> None:
    """RSPCA Assured mandates <=15 s stun-to-bleed for salmon/trout."""
    for key in ("atlantic_salmon", "rainbow_trout"):
        profile = species.get_profile(key)
        assert profile is not None
        assert profile.max_stun_to_bleed_s == 15.0


def test_recovery_onset_is_positive_for_all_profiles() -> None:
    """Sanity invariant across the whole library."""
    for key in species.all_keys():
        profile = species.get_profile(key)
        assert profile is not None
        assert profile.recovery_onset_s > 0

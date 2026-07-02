"""Species recovery-threshold & electrical-stun-spec library.

The cited evidence base the verification engine enforces. Every threshold is traceable to a
source (a number without a source is a rumor). Where the field has **no published spec**
(gilthead sea bream electrical parameters), that gap is encoded honestly as ``None`` /
``electrical_spec_published=False`` — never invented — so the engine fails safe rather than
certifying against a fabricated number.

Figures tagged ``needs-primary`` in the notes were sourced from secondary syntheses during
scouting and MUST be traced to the primary PDF before any grant-facing claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SpeciesProfile:
    """Validated welfare thresholds for one species.

    ``recovery_onset_s`` is the earliest documented onset of recovery signs after an
    electrical stun — the hard threshold the recovery-clock enforces (kill/bleed before this).
    ``max_stun_to_bleed_s`` is a certifier-mandated interval (e.g. RSPCA ≤15 s) where one exists.
    A ``None`` electrical field/duration means *no published spec* — the engine treats that as
    un-verifiable (UNCERTAIN), not as "anything passes".
    """

    key: str
    common_name: str
    scientific_name: str
    water: str  # "fresh" | "sea"
    recovery_onset_s: float
    recovery_onset_confidence: str  # "high" | "moderate" | "low" | "needs-primary"
    max_stun_to_bleed_s: float | None
    min_field_strength_v_per_cm: float | None
    min_duration_s: float | None
    frequency_hz: float | None
    electrical_spec_published: bool
    nominal_conductivity_us_cm: float | None
    notes: str
    sources: tuple[str, ...] = field(default_factory=tuple)

    def hard_recovery_limit_s(self) -> float:
        """The interval beyond which a fish risks waking before death.

        The stricter of the certifier stun-to-bleed limit (if any) and the documented
        recovery onset — fail-safe: we enforce the tighter bound.
        """
        if self.max_stun_to_bleed_s is not None:
            return min(self.max_stun_to_bleed_s, self.recovery_onset_s)
        return self.recovery_onset_s


_PROFILES: dict[str, SpeciesProfile] = {
    "atlantic_salmon": SpeciesProfile(
        key="atlantic_salmon",
        common_name="Atlantic salmon",
        scientific_name="Salmo salar",
        water="sea",
        recovery_onset_s=44.0,
        recovery_onset_confidence="high",
        max_stun_to_bleed_s=15.0,
        min_field_strength_v_per_cm=1.0,
        min_duration_s=1.0,
        frequency_hz=50.0,
        electrical_spec_published=True,
        nominal_conductivity_us_cm=35000.0,
        notes=(
            "Recovery signs (weak EEG primary responses) between 44 and 443 s after the field; "
            "44 s is the earliest onset, NOT a universal safe duration. RSPCA Assured: ≤15 s "
            "stun-to-bleed. Seawater (~35,000 µS/cm) needs higher current density."
        ),
        sources=(
            "Lambooij et al. 2010, Aquaculture 300:107-112",
            "Lines & Kestin 2004, Aquaculture 241:219-234",
            "RSPCA Assured Welfare Standards for Farmed Atlantic Salmon 2024",
        ),
    ),
    "rainbow_trout": SpeciesProfile(
        key="rainbow_trout",
        common_name="Rainbow trout",
        scientific_name="Oncorhynchus mykiss",
        water="fresh",
        recovery_onset_s=30.0,
        recovery_onset_confidence="moderate",
        max_stun_to_bleed_s=15.0,
        min_field_strength_v_per_cm=3.0,
        min_duration_s=1.0,
        frequency_hz=1000.0,
        electrical_spec_published=True,
        nominal_conductivity_us_cm=400.0,
        notes=(
            "More favourable than marine species (some studies >70% insensible ≥15 min) but a "
            "material fraction recover quickly; ~30 s sustained current can cause death by anoxia "
            "before recovery. ~100 mA / 50 Hz / ≥1 s is an effective-stun datum; 1000 Hz reduces "
            "carcass damage. ~3 V/cm in fresh water (Lines & Kestin)."
        ),
        sources=(
            "Lines & Kestin 2004, Aquaculture 241:219-234",
            "HSA — Electrical Stunning of Fish",
            "RSPCA Assured Welfare Standards for Farmed Rainbow Trout 2025",
        ),
    ),
    "european_sea_bass": SpeciesProfile(
        key="european_sea_bass",
        common_name="European sea bass",
        scientific_name="Dicentrarchus labrax",
        water="sea",
        recovery_onset_s=120.0,
        recovery_onset_confidence="needs-primary",
        max_stun_to_bleed_s=None,
        min_field_strength_v_per_cm=1.0,
        min_duration_s=1.0,
        frequency_hz=50.0,
        electrical_spec_published=True,
        nominal_conductivity_us_cm=50000.0,
        notes=(
            "Reported to recover sensibility in ~2 min while commercial slaughter takes 5-50 min "
            "to kill — a large recovery-before-death window [needs-primary]. Electrical evidence "
            "sparse: few lab studies, no field trials. Spec partly extrapolated."
        ),
        sources=(
            "Rethink Priorities 2023 (EA Forum) — synthesis of tier-1 lab work [needs-primary]",
            "Lines & Kestin 2004, Aquaculture 241:219-234",
        ),
    ),
    "gilthead_sea_bream": SpeciesProfile(
        key="gilthead_sea_bream",
        common_name="Gilthead sea bream",
        scientific_name="Sparus aurata",
        water="sea",
        recovery_onset_s=120.0,
        recovery_onset_confidence="needs-primary",
        max_stun_to_bleed_s=None,
        min_field_strength_v_per_cm=None,  # NO published spec — the field's biggest gap
        min_duration_s=None,
        frequency_hz=None,
        electrical_spec_published=False,
        nominal_conductivity_us_cm=50000.0,
        notes=(
            "The field's single biggest evidence gap: gilthead sea bream has NO published measured "
            "electrical-stunning spec — industry extrapolates from sea bass. The engine therefore "
            "CANNOT verify dose for bream and must return UNCERTAIN on dose. Recovery ~2 min "
            "[needs-primary]. This species is the strongest case for the project's open-spec work."
        ),
        sources=(
            "research/technical-context.md (project SoA map, 2026-06-19)",
            "Rethink Priorities 2023 (EA Forum) [needs-primary]",
        ),
    ),
    "common_carp": SpeciesProfile(
        key="common_carp",
        common_name="Common carp",
        scientific_name="Cyprinus carpio",
        water="fresh",
        recovery_onset_s=48.0,
        recovery_onset_confidence="moderate",
        max_stun_to_bleed_s=None,
        min_field_strength_v_per_cm=3.0,
        min_duration_s=5.0,
        frequency_hz=50.0,
        electrical_spec_published=True,
        nominal_conductivity_us_cm=600.0,
        notes=(
            "Unconscious at ~0.73 A/dm² for 5 s; fin movements resumed at 48±8 s, swimming at "
            "121±83 s. Recovery onset (fin movement) = 48 s used as the hard limit."
        ),
        sources=("Carp electrical-stunning lab study (per scouting; trace primary)",),
    ),
    "nile_tilapia": SpeciesProfile(
        key="nile_tilapia",
        common_name="Nile tilapia",
        scientific_name="Oreochromis niloticus",
        water="fresh",
        recovery_onset_s=60.0,
        recovery_onset_confidence="low",
        max_stun_to_bleed_s=None,
        min_field_strength_v_per_cm=None,  # electrically resistant — percussion advised
        min_duration_s=None,
        frequency_hz=None,
        electrical_spec_published=False,
        nominal_conductivity_us_cm=700.0,
        notes=(
            "Electrically resistant — percussion is advised; a humane electrical protocol exists "
            "(~1.0 Arms/dm² at 700 µS/cm) but is borderline. Electrical dose treated as "
            "un-verifiable here (UNCERTAIN); recovery onset conservative."
        ),
        sources=("Tilapia humane-slaughter protocol literature (per scouting; trace primary)",),
    ),
}


def get_profile(key: str) -> SpeciesProfile | None:
    """Return the profile for ``key``, or ``None`` if unknown.

    Fail-safe: an unknown species resolves to ``None`` (never to defaults), so the engine
    cannot certify a fish it has no validated thresholds for.
    """
    return _PROFILES.get(key)


def all_keys() -> list[str]:
    """All species keys in the library, sorted for stable output."""
    return sorted(_PROFILES)

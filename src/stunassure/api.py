"""StunAssure HTTP API — a thin, optional service layer over the zero-dependency core.

The verification core (:mod:`stunassure.engine`, :mod:`stunassure.sampling`,
:mod:`stunassure.report`) has **no runtime dependencies** and must stay that way — it has to run
on the poorest vessel, offline. This module is the *optional* cloud/edge service tier: install the
``api`` extra (``pip install 'stunassure[api]'``) to expose the same logic over HTTP for a
dashboard, a certifier export, or fleet aggregation.

Endpoints (see ``docs/api.md``):

* ``GET  /health``                — liveness probe
* ``GET  /species``               — the cited species threshold library
* ``GET  /species/{key}``         — one species profile
* ``POST /verify``                — verify a single stun event → PASS / UNCERTAIN / FAIL
* ``POST /reports``               — verify a batch sample + certify the lot → signed report
* ``POST /reports/verify``        — check a report's SHA-256 signature (tamper detection)
* ``POST /demo``                  — simulate + verify + certify a batch → signed report (CLI parity)
* ``GET  /ui/``                   — the static web dashboard (a client of the endpoints above)

The API never weakens the fail-safe contract: it is a transport, not a second decision path. The
dashboard is a client only — the verdict is always computed by the core.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import RedirectResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via import guard test
    raise ModuleNotFoundError(
        "The StunAssure API extra is not installed. Install it with: "
        "pip install 'stunassure[api]'"
    ) from exc

from . import __version__, species
from .engine import StunEvent, verify
from .report import build_report, verify_report
from .sampling import design_plan
from .simulator import simulate_batch

_WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(
    title="StunAssure API",
    version=__version__,
    summary="Prove, cheaply and fail-safe, that each batch of fish was rendered insensible.",
    description=__doc__,
)


# --------------------------------------------------------------------------- models
class StunEventIn(BaseModel):
    """One stun measurement. Any omitted field means 'not measured' → treated as un-verifiable."""

    species_key: str = Field(examples=["atlantic_salmon"])
    field_strength_v_per_cm: float | None = None
    stun_duration_s: float | None = None
    frequency_hz: float | None = None
    stun_to_bleed_s: float | None = None
    water_conductivity_us_cm: float | None = None
    evoked_response_suppressed: bool | None = None
    sample_id: str = ""

    def to_event(self) -> StunEvent:
        return StunEvent(
            species_key=self.species_key,
            field_strength_v_per_cm=self.field_strength_v_per_cm,
            stun_duration_s=self.stun_duration_s,
            frequency_hz=self.frequency_hz,
            stun_to_bleed_s=self.stun_to_bleed_s,
            water_conductivity_us_cm=self.water_conductivity_us_cm,
            evoked_response_suppressed=self.evoked_response_suppressed,
            sample_id=self.sample_id,
        )


class LayerFindingOut(BaseModel):
    layer: str
    verdict: str
    reason: str


class VerifyOut(BaseModel):
    verdict: str
    findings: list[LayerFindingOut]


class ReportRequest(BaseModel):
    """A batch sample to verify and certify against a lot."""

    species_key: str = Field(examples=["atlantic_salmon"])
    sample: list[StunEventIn]
    lot_size: int = Field(gt=0, examples=[50000])
    aql: float = Field(default=0.065, gt=0.0, lt=1.0)
    target_confidence: float = Field(default=0.95, gt=0.0, lt=1.0)
    generated_at: str = Field(
        description="ISO-8601 timestamp; passed in for deterministic, reproducible signatures.",
        examples=["2026-06-19T12:00:00Z"],
    )


class DemoRequest(BaseModel):
    """Generate a reproducible synthetic batch, verify + certify it, and return a signed report.

    This mirrors the ``stunassure demo`` CLI and lets the dashboard exercise the whole stack with
    zero hardware and zero live fish.
    """

    species_key: str = Field(default="atlantic_salmon", examples=["atlantic_salmon"])
    lot_size: int = Field(default=50000, gt=0)
    seed: int = 1
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    aql: float = Field(default=0.065, gt=0.0, lt=1.0)
    target_confidence: float = Field(default=0.95, gt=0.0, lt=1.0)
    generated_at: str = Field(
        default="2026-06-19T12:00:00Z",
        description="ISO-8601 timestamp; passed in for deterministic, reproducible signatures.",
    )


class SignatureCheck(BaseModel):
    valid: bool


# --------------------------------------------------------------------------- routes
@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Liveness probe for load balancers / Kubernetes."""
    return {"status": "ok", "version": __version__}


@app.get("/species", tags=["species"])
def list_species() -> list[dict[str, Any]]:
    """The cited species threshold library the engine enforces."""
    out: list[dict[str, Any]] = []
    for key in species.all_keys():
        p = species.get_profile(key)
        assert p is not None
        out.append(
            {
                "key": p.key,
                "common_name": p.common_name,
                "scientific_name": p.scientific_name,
                "water": p.water,
                "recovery_onset_s": p.recovery_onset_s,
                "hard_recovery_limit_s": p.hard_recovery_limit_s(),
                "electrical_spec_published": p.electrical_spec_published,
            }
        )
    return out


@app.get("/species/{key}", tags=["species"])
def get_species(key: str) -> dict[str, Any]:
    """One species profile, including sources. 404 if the species is unknown."""
    p = species.get_profile(key)
    if p is None:
        raise HTTPException(status_code=404, detail=f"unknown species '{key}'")
    return {
        "key": p.key,
        "common_name": p.common_name,
        "scientific_name": p.scientific_name,
        "water": p.water,
        "recovery_onset_s": p.recovery_onset_s,
        "recovery_onset_confidence": p.recovery_onset_confidence,
        "max_stun_to_bleed_s": p.max_stun_to_bleed_s,
        "hard_recovery_limit_s": p.hard_recovery_limit_s(),
        "min_field_strength_v_per_cm": p.min_field_strength_v_per_cm,
        "min_duration_s": p.min_duration_s,
        "frequency_hz": p.frequency_hz,
        "electrical_spec_published": p.electrical_spec_published,
        "nominal_conductivity_us_cm": p.nominal_conductivity_us_cm,
        "notes": p.notes,
        "sources": list(p.sources),
    }


@app.post("/verify", response_model=VerifyOut, tags=["verify"])
def verify_event(event: StunEventIn) -> VerifyOut:
    """Verify a single stun event → fail-safe PASS / UNCERTAIN / FAIL with per-layer reasons."""
    result = verify(event.to_event())
    return VerifyOut(
        verdict=result.verdict.label,
        findings=[
            LayerFindingOut(layer=f.layer, verdict=f.verdict.label, reason=f.reason)
            for f in result.findings
        ],
    )


@app.post("/reports", tags=["reports"])
def create_report(req: ReportRequest) -> dict[str, Any]:
    """Verify a batch sample, certify the lot by Welfare-by-Sampling, return a signed report."""
    if species.get_profile(req.species_key) is None:
        raise HTTPException(status_code=404, detail=f"unknown species '{req.species_key}'")
    return build_report(
        species_key=req.species_key,
        sample_events=[e.to_event() for e in req.sample],
        lot_size=req.lot_size,
        aql=req.aql,
        target_confidence=req.target_confidence,
        generated_at=req.generated_at,
    )


@app.post("/reports/verify", response_model=SignatureCheck, tags=["reports"])
def check_report(report: dict[str, Any]) -> SignatureCheck:
    """Return whether a report's SHA-256 signature matches its content (tamper detection)."""
    return SignatureCheck(valid=verify_report(report))


@app.post("/demo", tags=["reports"])
def run_demo(req: DemoRequest) -> dict[str, Any]:
    """Simulate a batch, verify + certify it, and return a signed report (mirrors the CLI demo)."""
    if species.get_profile(req.species_key) is None:
        raise HTTPException(status_code=404, detail=f"unknown species '{req.species_key}'")
    plan = design_plan(req.lot_size, req.aql, req.target_confidence)
    sample = simulate_batch(
        req.species_key, n=plan.sample_size, seed=req.seed, failure_rate=req.failure_rate
    )
    return build_report(
        species_key=req.species_key,
        sample_events=sample,
        lot_size=req.lot_size,
        aql=req.aql,
        target_confidence=req.target_confidence,
        generated_at=req.generated_at,
    )


# --------------------------------------------------------------------------- static dashboard
# A dependency-free, single-file UI that talks to the API above. The dashboard is a client only —
# it cannot bypass or weaken the fail-safe verdict, which is always computed by the core.
@app.get("/", include_in_schema=False)
def _root() -> RedirectResponse:
    return RedirectResponse(url="/ui/")


app.mount("/ui", StaticFiles(directory=str(_WEB_DIR), html=True), name="ui")

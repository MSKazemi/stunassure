"""Tests for the optional FastAPI service layer.

Skipped cleanly if the ``api`` extra (fastapi) is not installed, so the core test suite still
runs on a zero-dependency install.
"""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from stunassure import __version__  # noqa: E402
from stunassure.api import app  # noqa: E402

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": __version__}


def test_list_species() -> None:
    r = client.get("/species")
    assert r.status_code == 200
    keys = {s["key"] for s in r.json()}
    assert "atlantic_salmon" in keys
    assert "gilthead_sea_bream" in keys


def test_get_species_ok() -> None:
    r = client.get("/species/atlantic_salmon")
    assert r.status_code == 200
    body = r.json()
    assert body["common_name"] == "Atlantic salmon"
    assert body["electrical_spec_published"] is True
    assert body["sources"]


def test_get_species_unknown_404() -> None:
    r = client.get("/species/loch_ness_monster")
    assert r.status_code == 404


def test_verify_pass() -> None:
    r = client.post(
        "/verify",
        json={
            "species_key": "atlantic_salmon",
            "field_strength_v_per_cm": 2.0,
            "stun_duration_s": 2.0,
            "stun_to_bleed_s": 5.0,
            "evoked_response_suppressed": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["verdict"] == "PASS"


def test_verify_fail_on_recovery_breach() -> None:
    r = client.post(
        "/verify",
        json={
            "species_key": "atlantic_salmon",
            "field_strength_v_per_cm": 2.0,
            "stun_duration_s": 2.0,
            "stun_to_bleed_s": 999.0,
        },
    )
    assert r.status_code == 200
    assert r.json()["verdict"] == "FAIL"


def test_verify_uncertain_no_spec_species() -> None:
    r = client.post(
        "/verify",
        json={"species_key": "gilthead_sea_bream", "stun_to_bleed_s": 5.0},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "UNCERTAIN"
    layers = {f["layer"]: f["verdict"] for f in body["findings"]}
    assert layers["dose"] == "UNCERTAIN"


def test_reports_certify_and_signature_roundtrip() -> None:
    payload = {
        "species_key": "atlantic_salmon",
        "lot_size": 50000,
        "aql": 0.065,
        "target_confidence": 0.95,
        "generated_at": "2026-06-19T12:00:00Z",
        "sample": [
            {
                "species_key": "atlantic_salmon",
                "field_strength_v_per_cm": 2.0,
                "stun_duration_s": 2.0,
                "stun_to_bleed_s": 5.0,
                "sample_id": f"S-{i}",
            }
            for i in range(45)
        ],
    }
    r = client.post("/reports", json=payload)
    assert r.status_code == 200
    report = r.json()
    assert report["certification"]["accepted"] is True

    # The signature must verify, and any tampering must be detected.
    rv = client.post("/reports/verify", json=report)
    assert rv.status_code == 200
    assert rv.json() == {"valid": True}

    report["lot_size"] = 1  # tamper
    rv2 = client.post("/reports/verify", json=report)
    assert rv2.json() == {"valid": False}


def test_reports_unknown_species_404() -> None:
    r = client.post(
        "/reports",
        json={
            "species_key": "nope",
            "lot_size": 100,
            "generated_at": "2026-06-19T12:00:00Z",
            "sample": [],
        },
    )
    assert r.status_code == 404
